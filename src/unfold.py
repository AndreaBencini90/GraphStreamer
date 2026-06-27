"""GraphStreamer - Unfold: nodes collapse to center then reveal to final positions."""

import time
import sys
import json
import os

import requests
import yaml


def get_graph(base_url):
    nodes = {}
    edges = {}
    try:
        r = requests.get(f"{base_url}?operation=getGraph", timeout=(3, 10), stream=True)
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            data = json.loads(line)
            if "an" in data:
                for nid, attrs in data["an"].items():
                    nodes[nid] = attrs
            if "ae" in data:
                for eid, attrs in data["ae"].items():
                    edges[eid] = attrs
    except requests.exceptions.ReadTimeout:
        pass
    except Exception as e:
        print(f"Errore lettura grafo: {e}")
    return nodes, edges


def send_positions(base_url, updates):
    payload = {"cn": updates}
    try:
        requests.post(f"{base_url}?operation=updateGraph", json=payload, timeout=0.5)
    except requests.RequestException:
        pass


def lerp(a, b, t):
    return a + (b - a) * t


def order_nodes_by_groups(node_ids, labels, phases):
    """
    Return node_ids reordered according to label_groups in phases.
    Nodes matching a phase's label_groups come first (in phase order),
    unmatched nodes go at the end.
    """
    assigned = set()
    ordered = []

    for ph in phases:
        groups = ph.get("label_groups", [])
        if not groups:
            continue
        group_nodes = []
        for nid in node_ids:
            if nid in assigned:
                continue
            label = labels.get(nid, "").lower()
            if any(g.lower() in label for g in groups):
                group_nodes.append(nid)
                assigned.add(nid)
        ordered.extend(group_nodes)

    # Remaining nodes not matched by any group
    for nid in node_ids:
        if nid not in assigned:
            ordered.append(nid)

    return ordered


def build_start_times(node_ids, phases):
    """
    Assign start_time to each node based on phases.
    Each phase has nodes_per_second and duration_seconds.
    Nodes fill phases in order until duration runs out or all nodes placed.
    """
    n = len(node_ids)
    start_times = {}
    t_offset = 0.0
    node_offset = 0

    for ph in phases:
        nps = ph["nodes_per_second"]
        dur = ph["duration_seconds"]
        capacity = int(nps * dur)
        capacity = min(capacity, n - node_offset)
        if capacity <= 0:
            t_offset += dur
            continue

        for j in range(capacity):
            nid = node_ids[node_offset + j]
            start_times[nid] = t_offset + j / nps

        t_offset += dur
        node_offset += capacity
        if node_offset >= n:
            break

    # Remaining nodes placed at end
    for i in range(node_offset, n):
        start_times[node_ids[i]] = t_offset + (i - node_offset) / phases[-1]["nodes_per_second"]

    total = max(start_times.values()) if start_times else 0
    return start_times, total


def run(config_path):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    gephi_cfg = cfg["gephi"]
    unfold_cfg = cfg["unfold"]

    base_url = f"http://{gephi_cfg['host']}:{gephi_cfg['port']}/{gephi_cfg['workspace']}"

    fps = unfold_cfg.get("fps", 10)
    transition_seconds = unfold_cfg.get("transition_seconds", 0.8)
    scale = unfold_cfg.get("scale", 1.0)
    snapshot_file = unfold_cfg.get("snapshot_file", "unfold_positions.json")
    refresh = unfold_cfg.get("refresh_positions", False)
    phases = unfold_cfg.get("phases", [{"nodes_per_second": 10, "duration_seconds": 60}])

    # Load or read positions
    if os.path.exists(snapshot_file) and not refresh:
        print(f"Carico posizioni da {snapshot_file}...")
        with open(snapshot_file) as f:
            final_pos = json.load(f)
        node_ids = list(final_pos.keys())
        print(f"{len(node_ids)} nodi caricati.")
    else:
        if refresh:
            print("refresh_positions: true — rileggo il layout da Gephi...")
        else:
            print(f"Nessuno snapshot trovato, leggo da Gephi...")
        nodes, edges = get_graph(base_url)
        if not nodes:
            print("Nessun nodo trovato! Carica un grafo in Gephi prima di lanciare.")
            sys.exit(1)
        node_ids = list(nodes.keys())
        group_by_field = unfold_cfg.get("group_by", "Molecule")
        final_pos = {
            nid: {
                "x": nodes[nid].get("x", 0) * scale,
                "y": nodes[nid].get("y", 0) * scale,
                "group": nodes[nid].get(group_by_field, ""),
            }
            for nid in node_ids
        }
        with open(snapshot_file, "w") as f:
            json.dump(final_pos, f)
        print(f"Salvati {len(node_ids)} nodi in {snapshot_file}.")

    n = len(node_ids)
    cx = sum(p["x"] for p in final_pos.values()) / n
    cy = sum(p["y"] for p in final_pos.values()) / n

    # Riordina nodi in base ai label_groups nelle fasi
    labels = {nid: final_pos[nid].get("group", "") for nid in node_ids}
    has_groups = any("label_groups" in ph for ph in phases)
    no_labels = all(v == "" for v in labels.values())

    if has_groups and no_labels:
        print("  [!] Snapshot senza dati molecola — imposta refresh_positions: true e rilancia una volta.")
    elif has_groups:
        node_ids = order_nodes_by_groups(node_ids, labels, phases)
        for ph in phases:
            groups = ph.get("label_groups", [])
            if groups:
                count = sum(1 for nid in node_ids
                           if any(g.lower() in labels.get(nid,"").lower() for g in groups))
                print(f"  gruppo {groups}: {count} nodi")

    start_times, total_duration = build_start_times(node_ids, phases)

    print(f"\nHo in memoria {n} nodi e {len(phases)} fasi.")
    t_off = 0
    for i, ph in enumerate(phases):
        cap = int(ph["nodes_per_second"] * ph["duration_seconds"])
        print(f"  fase {i+1}: {ph['nodes_per_second']} nodi/sec per {ph['duration_seconds']}s  (~{cap} nodi, da t={t_off:.0f}s)")
        t_off += ph["duration_seconds"]
    print(f"  durata stimata: {total_duration:.0f}s\n")

    print("Raccolgo tutto al centro...")
    send_positions(base_url, {nid: {"x": cx, "y": cy} for nid in node_ids})
    time.sleep(0.5)

    print("Comincio a dispiegare la struttura.\n")
    frame_interval = 1.0 / fps
    t_start = time.perf_counter()
    done = set()
    last_log = -5

    # Frasi per soglia percentuale nodi arrivati
    phrases = [
        (0,   "prima della forma c'e' solo attesa"),
        (3,   "qualcosa si muove nel disordine"),
        (8,   "probabilita' che si coagula"),
        (20,  "i nodi cercano il loro posto nello spazio"),
        (35,  "le tensioni iniziano a parlarsi"),
        (50,  "le tensioni trovano equilibrio"),
        (65,  "il caso ha gia' deciso, noi ancora no"),
        (78,  "stiamo ad osservare cosa sta decidendo"),
        (90,  "la forma era gia' li', adesso si vede"),
        (97,  "il grafo e' tornato"),
    ]

    def get_phrase(pct):
        current = phrases[0][1]
        for threshold, text in phrases:
            if pct * 100 >= threshold:
                current = text
        return current

    try:
        while True:
            now = time.perf_counter() - t_start
            if now >= total_duration + transition_seconds:
                break

            updates = {}
            for nid in node_ids:
                if nid in done:
                    continue
                t_node = now - start_times[nid]
                if t_node < 0:
                    continue
                t = t_node / transition_seconds
                if t >= 1.0:
                    done.add(nid)
                    updates[nid] = {"x": final_pos[nid]["x"], "y": final_pos[nid]["y"]}
                else:
                    t_ease = 1 - (1 - t) ** 3
                    updates[nid] = {
                        "x": lerp(cx, final_pos[nid]["x"], t_ease),
                        "y": lerp(cy, final_pos[nid]["y"], t_ease),
                    }

            if updates:
                send_positions(base_url, updates)

            if now - last_log >= 5:
                arrived = len(done)
                pct = arrived / n
                bar = int(pct * 20)
                progress = "[" + "#" * bar + "." * (20 - bar) + "]"
                comment = get_phrase(pct)
                print(f"  {progress}  {arrived}/{n}  —  {comment}")
                last_log = now

            time.sleep(frame_interval)

    except KeyboardInterrupt:
        print("\nInterrotto.")
        return

    print(f"\nTutti i {n} nodi sono tornati al loro posto.")


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_config = os.path.join(root, "config", "unfold.yaml")
    config = sys.argv[1] if len(sys.argv) > 1 else default_config
    os.chdir(root)  # snapshot e altri path relativi funzionano dalla root
    run(config)
