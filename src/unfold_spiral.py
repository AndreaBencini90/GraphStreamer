"""
GraphStreamer - Unfold Spiral
Posiziona i nodi su una spirale di Archimede, raggruppati per gruppo (es. era geologica).
Le posizioni vengono calcolate matematicamente (non da ForceAtlas).

Uso:
    .\\venv\\Scripts\\python src\\unfold_spiral.py
    .\\venv\\Scripts\\python src\\unfold_spiral.py config\\mio_config.yaml
"""

import time
import sys
import json
import os
import math

import requests
import yaml


# ---------------------------------------------------------------------------
# Lettura grafo da Gephi
# ---------------------------------------------------------------------------

def get_graph(base_url):
    """
    Legge tutti i nodi da Gephi via getGraph.
    Strategia: legge a round da 5s finche' il conteggio non si stabilizza
    (getGraph manda prima tutti i nodi esistenti, poi resta aperto per live updates).
    """
    nodes = {}
    prev_count = -1
    stable_rounds = 0

    while stable_rounds < 3:
        try:
            r = requests.get(f"{base_url}?operation=getGraph", timeout=(3, 8), stream=True)
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "an" in data:
                    for nid, attrs in data["an"].items():
                        nodes[nid] = attrs
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            pass
        except Exception as e:
            print(f"Errore lettura grafo: {e}")
            break

        count = len(nodes)
        if count == prev_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
        prev_count = count
        if count > 0:
            print(f"  letti {count} nodi...", flush=True)

    return nodes


def send_positions(base_url, updates):
    payload = {"cn": updates}
    try:
        requests.post(f"{base_url}?operation=updateGraph", json=payload, timeout=0.5)
    except requests.RequestException:
        pass


# ---------------------------------------------------------------------------
# Calcolo spirale di Archimede
# ---------------------------------------------------------------------------

def compute_spiral_positions(groups, spiral_cfg):
    """
    Distribuisce i gruppi di nodi lungo una spirale di Archimede.

    groups: lista di (nome_gruppo, [node_id, ...]) in ordine di fase
    spiral_cfg: dizionario con parametri spirale dal yaml

    Ritorna: {node_id: (x, y)}
    """
    r_min       = spiral_cfg.get("r_min", 80)
    r_max       = spiral_cfg.get("r_max", 900)
    turns       = spiral_cfg.get("turns", 3.5)
    gap_deg     = spiral_cfg.get("gap_angle_deg", 20)
    rotation_deg = spiral_cfg.get("rotation_deg", -90)

    total_angle = turns * 2 * math.pi
    gap_rad     = math.radians(gap_deg)
    rot_rad     = math.radians(rotation_deg)

    total_nodes = sum(len(nids) for _, nids in groups)
    n_groups    = sum(1 for _, nids in groups if nids)
    total_gap   = n_groups * gap_rad
    usable      = total_angle - total_gap

    positions   = {}
    theta       = 0.0

    for group_name, node_ids in groups:
        n = len(node_ids)
        if n == 0:
            continue

        # arco proporzionale al numero di nodi in questo gruppo
        arc = usable * (n / total_nodes)

        for i, nid in enumerate(node_ids):
            # t = posizione normalizzata 0..1 dentro il gruppo
            t = i / max(n - 1, 1) if n > 1 else 0.0
            th = theta + t * arc

            # raggio cresce linearmente con l'angolo
            r = r_min + (r_max - r_min) * (th / total_angle)

            # applica rotazione globale
            angle = th + rot_rad
            positions[nid] = (r * math.cos(angle), r * math.sin(angle))

        theta += arc + gap_rad

    return positions


# ---------------------------------------------------------------------------
# Ordinamento nodi per fase/gruppo
# ---------------------------------------------------------------------------

def assign_groups(node_ids, molecule_map, phases, group_by_field):
    """
    Restituisce una lista ordinata di (nome_gruppo, [node_ids]) secondo le fasi.
    I nodi non assegnati vanno in fondo come gruppo 'altri'.
    """
    assigned = set()
    result   = []

    for ph in phases:
        labels = ph.get("label_groups", [])
        if not labels:
            continue
        group_name = " + ".join(labels)
        group_nodes = []
        for nid in node_ids:
            if nid in assigned:
                continue
            mol = molecule_map.get(nid, "").lower()
            if any(mol == lbl.lower() for lbl in labels):
                group_nodes.append(nid)
                assigned.add(nid)
        result.append((group_name, group_nodes))

    others = [nid for nid in node_ids if nid not in assigned]
    if others:
        result.append(("altri", others))

    return result


# ---------------------------------------------------------------------------
# Timing: quando parte ogni nodo
# ---------------------------------------------------------------------------

def build_start_times(groups, phases):
    """
    Assegna un tempo di partenza a ogni nodo.
    Ogni gruppo segue la velocita' della fase corrispondente.
    """
    start_times = {}
    t_offset    = 0.0

    # mappa nome_gruppo -> fase
    phase_by_group = {}
    for ph in phases:
        labels = ph.get("label_groups", [])
        if labels:
            name = " + ".join(labels)
            phase_by_group[name] = ph

    last_ph = phases[-1] if phases else {"nodes_per_second": 5, "duration_seconds": 60}

    for group_name, node_ids in groups:
        ph  = phase_by_group.get(group_name, last_ph)
        nps = ph["nodes_per_second"]
        for i, nid in enumerate(node_ids):
            start_times[nid] = t_offset + i / nps
        if node_ids:
            t_offset += len(node_ids) / nps + ph.get("gap_seconds", 1.0)

    total = max(start_times.values()) if start_times else 0
    return start_times, total


# ---------------------------------------------------------------------------
# Interpolazione e log
# ---------------------------------------------------------------------------

def lerp(a, b, t):
    return a + (b - a) * t


PHRASES = [
    (0,  "prima della vita, solo roccia e calore"),
    (3,  "i batteri respirano nell'oceano primordiale"),
    (10, "l'ossigeno avvelena il cielo e salva il futuro"),
    (20, "qualcosa inizia a diventare piu' di una cellula"),
    (35, "gli animali scoprono di avere una forma"),
    (50, "i dinosauri dominano per centinaia di milioni di anni"),
    (65, "una roccia, poi silenzio, poi i mammiferi"),
    (78, "qualcosa in piedi guarda l'orizzonte"),
    (93, "siamo quasi all'esterno della spirale"),
    (99, "homo sapiens: l'ultimo punto"),
]


def get_phrase(pct):
    current = PHRASES[0][1]
    for threshold, text in PHRASES:
        if pct * 100 >= threshold:
            current = text
    return current


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(config_path):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    gephi_cfg  = cfg["gephi"]
    unfold_cfg = cfg["unfold"]
    spiral_cfg = unfold_cfg.get("spiral", {})
    phases     = unfold_cfg.get("phases", [{"nodes_per_second": 10, "duration_seconds": 60}])

    base_url   = f"http://{gephi_cfg['host']}:{gephi_cfg['port']}/{gephi_cfg['workspace']}"
    group_by   = unfold_cfg.get("group_by", "Molecule")
    snap_file  = unfold_cfg.get("snapshot_file", "spiral_positions.json")
    refresh    = unfold_cfg.get("refresh_positions", False)
    fps        = unfold_cfg.get("fps", 10)
    transition = unfold_cfg.get("transition_seconds", 2.0)

    # --- Carica dati molecola ---
    molecule_map = {}  # nid -> valore Molecule

    if os.path.exists(snap_file) and not refresh:
        print(f"Carico snapshot da {snap_file}...")
        with open(snap_file) as f:
            snap = json.load(f)
        node_ids     = list(snap.keys())
        molecule_map = {nid: snap[nid].get("group", "") for nid in node_ids}
        spiral_pos   = {nid: (snap[nid]["x"], snap[nid]["y"]) for nid in node_ids}
        print(f"{len(node_ids)} nodi caricati.")
    else:
        if refresh:
            print("refresh_positions: true — leggo il grafo da Gephi...")
        else:
            print("Nessuno snapshot trovato, leggo da Gephi...")

        nodes = get_graph(base_url)
        if not nodes:
            print("Nessun nodo trovato! Gephi online? Master Server avviato? Workspace corretto?")
            print(f"  URL tentato: {base_url}?operation=getGraph")
            sys.exit(1)

        node_ids     = list(nodes.keys())
        molecule_map = {nid: nodes[nid].get(group_by, "") for nid in node_ids}
        scale        = unfold_cfg.get("scale", 1.0)
        pos_source   = unfold_cfg.get("position_source", "spiral")

        groups_ordered = assign_groups(node_ids, molecule_map, phases, group_by)

        if pos_source == "gephi":
            # Usa le coordinate x/y attuali di Gephi come destinazione
            print(f"Leggo posizioni reali da Gephi per {len(node_ids)} nodi...")
            spiral_pos = {
                nid: (nodes[nid].get("x", 0) * scale, nodes[nid].get("y", 0) * scale)
                for nid in node_ids
            }
        else:
            # Calcola posizioni matematicamente su spirale di Archimede
            print(f"Calcolo posizioni spirale per {len(node_ids)} nodi...")
            spiral_pos = compute_spiral_positions(groups_ordered, spiral_cfg)

        # Salva snapshot in ordine spirale (per gruppo, poi per raggio crescente)
        # cosi' il ricarico preserva l'ordine corretto senza sort aggiuntivi
        import math as _math
        def _r(nid):
            x, y = spiral_pos[nid]
            return _math.hypot(x, y)
        ordered_for_snap = [
            nid
            for _, gnids in groups_ordered
            for nid in sorted(gnids, key=_r)
        ]
        snap = {
            nid: {
                "x":     spiral_pos[nid][0],
                "y":     spiral_pos[nid][1],
                "group": molecule_map[nid],
            }
            for nid in ordered_for_snap
        }
        with open(snap_file, "w") as f:
            json.dump(snap, f, indent=2)
        print(f"Snapshot salvato in {snap_file} ({pos_source} positions).")

    # --- Verifica gruppi ---
    groups_ordered = assign_groups(node_ids, molecule_map, phases, group_by)
    print()
    for group_name, gnids in groups_ordered:
        print(f"  {group_name}: {len(gnids)} nodi")

    # Sort per raggio usando le posizioni REALI di Gephi.
    # Il raggio cresce monotonamente lungo l'arco della spirale reale,
    # quindi hypot(x,y) da' l'ordine corretto senza salti tra era e era.
    import math as _math
    groups_ordered = [
        (name, sorted(gnids, key=lambda nid: _math.hypot(spiral_pos[nid][0], spiral_pos[nid][1])))
        for name, gnids in groups_ordered
    ]

    # --- Timing ---
    start_times, total_duration = build_start_times(groups_ordered, phases)
    # Esclude "altri" da flat_order: non hanno fase associata e partirebbero a t=0
    flat_order = [nid for name, gnids in groups_ordered if name != "altri" for nid in gnids]

    print(f"\nDurata stimata: {total_duration:.0f}s\n")

    # --- Centro della spirale (0,0) ---
    cx, cy = 0.0, 0.0
    frame_interval = 1.0 / fps

    # Collassa in chunk grandi: meno request = meno latenza totale
    # chunk=2000 -> ~8 request, finisce in <2s. Due passate per sicurezza.
    # Aggiunge un blind sweep 0..max_id+10 per coprire nodi mancanti dallo stream.
    print("Collasso tutti i nodi al centro della spirale...")
    center_payload = {"x": cx, "y": cy}
    chunk_size = 2000
    max_id = max(int(nid) for nid in node_ids if nid.isdigit()) if node_ids else 0
    all_collapse_ids = list(dict.fromkeys(node_ids + [str(i) for i in range(max_id + 50)]))
    for _ in range(3):
        for i in range(0, len(all_collapse_ids), chunk_size):
            chunk = all_collapse_ids[i:i + chunk_size]
            try:
                requests.post(
                    f"{base_url}?operation=updateGraph",
                    json={"cn": {nid: center_payload for nid in chunk}},
                    timeout=8.0,
                )
            except requests.RequestException:
                pass
    initial_delay = unfold_cfg.get("initial_delay", 2.0)
    time.sleep(initial_delay)

    print("Inizio rivelazione a spirale.\n")
    frame_interval = 1.0 / fps
    t_start        = time.perf_counter()
    done           = set()
    last_log       = -5.0
    n              = len(node_ids)

    try:
        while True:
            now = time.perf_counter() - t_start
            if now >= total_duration + transition:
                break

            updates = {}
            for nid in flat_order:
                if nid in done:
                    continue
                t_node = now - start_times.get(nid, 0)
                if t_node < 0:
                    continue
                tx, ty = spiral_pos[nid]
                t = t_node / transition
                if t >= 1.0:
                    done.add(nid)
                    updates[nid] = {"x": tx, "y": ty}
                else:
                    ease = 1 - (1 - t) ** 3
                    updates[nid] = {
                        "x": lerp(cx, tx, ease),
                        "y": lerp(cy, ty, ease),
                    }

            if updates:
                send_positions(base_url, updates)

            if now - last_log >= 5:
                pct  = len(done) / n
                bar  = int(pct * 20)
                prog = "[" + "#" * bar + "." * (20 - bar) + "]"
                print(f"  {prog}  {len(done)}/{n}  —  {get_phrase(pct)}")
                last_log = now

            time.sleep(frame_interval)

    except KeyboardInterrupt:
        print("\nInterrotto.")
        return

    print(f"\nTutti i {n} nodi sono sulla spirale.")


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_config = os.path.join(root, "config", "unfold_spiral.yaml")
    config = sys.argv[1] if len(sys.argv) > 1 else default_config
    os.chdir(root)
    run(config)
