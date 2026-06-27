"""GraphStreamer - Pulse: reads graph from Gephi, applies force-directed pulsing."""

import time
import sys
import json
import math

import requests
import yaml


def get_graph(base_url):
    """Read current graph from Gephi streaming endpoint."""
    nodes = {}
    edges = {}
    try:
        r = requests.get(f"{base_url}?operation=getGraph", timeout=(3, 2), stream=True)
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
        pass  # stream ended by timeout — that's expected
    except Exception as e:
        print(f"Errore lettura grafo: {e}")
    return nodes, edges


def compute_forces(nodes, edges, repulsion, attraction):
    """Compute force-directed displacement for each node."""
    forces = {nid: [0.0, 0.0] for nid in nodes}
    node_list = list(nodes.keys())

    # Repulsion between all pairs
    for i, n1 in enumerate(node_list):
        x1 = nodes[n1].get("x", 0)
        y1 = nodes[n1].get("y", 0)
        for n2 in node_list[i+1:]:
            x2 = nodes[n2].get("x", 0)
            y2 = nodes[n2].get("y", 0)
            dx = x1 - x2
            dy = y1 - y2
            dist = math.sqrt(dx*dx + dy*dy) + 0.01
            force = repulsion / (dist * dist)
            fx = (dx / dist) * force
            fy = (dy / dist) * force
            forces[n1][0] += fx
            forces[n1][1] += fy
            forces[n2][0] -= fx
            forces[n2][1] -= fy

    # Attraction along edges
    for eid, eattrs in edges.items():
        src = eattrs.get("source")
        tgt = eattrs.get("target")
        if src in nodes and tgt in nodes:
            x1 = nodes[src].get("x", 0)
            y1 = nodes[src].get("y", 0)
            x2 = nodes[tgt].get("x", 0)
            y2 = nodes[tgt].get("y", 0)
            dx = x2 - x1
            dy = y2 - y1
            dist = math.sqrt(dx*dx + dy*dy) + 0.01
            force = dist * attraction
            fx = (dx / dist) * force
            fy = (dy / dist) * force
            forces[src][0] += fx
            forces[src][1] += fy
            forces[tgt][0] -= fx
            forces[tgt][1] -= fy

    return forces


def update_positions(base_url, nodes, forces, damping=0.1):
    """Apply forces to node positions and send to Gephi."""
    payload = {"an": {}}
    for nid in nodes:
        nodes[nid]["x"] = nodes[nid].get("x", 0) + forces[nid][0] * damping
        nodes[nid]["y"] = nodes[nid].get("y", 0) + forces[nid][1] * damping
        payload["an"][nid] = {"x": nodes[nid]["x"], "y": nodes[nid]["y"]}

    try:
        requests.post(f"{base_url}?operation=updateGraph", json=payload, timeout=0.5)
    except requests.RequestException:
        pass


def run(config_path):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    gephi_cfg = cfg["gephi"]
    pulse_cfg = cfg["pulse"]

    base_url = f"http://{gephi_cfg['host']}:{gephi_cfg['port']}/{gephi_cfg['workspace']}"

    duration = pulse_cfg["duration_seconds"]
    bpm = pulse_cfg["bpm"]
    repulsion_min = pulse_cfg["repulsion_min"]
    repulsion_max = pulse_cfg["repulsion_max"]
    attraction = pulse_cfg["attraction"]

    beat_interval = 60.0 / bpm

    # Read graph from Gephi
    print(f"Reading graph from {base_url}...")
    nodes, edges = get_graph(base_url)

    if not nodes:
        print("Nessun nodo trovato! Carica un grafo in Gephi prima di lanciare.")
        sys.exit(1)

    print(f"Found {len(nodes)} nodes, {len(edges)} edges.")
    print(f"Pulsing at {bpm} BPM for {duration}s. Press Ctrl+C to stop.")

    t_start = time.perf_counter()
    frame_interval = 1.0 / pulse_cfg.get("fps", 30)

    try:
        while True:
            elapsed = time.perf_counter() - t_start
            if elapsed >= duration:
                break

            # Pulse: repulsion oscillates with the beat
            beat_phase = (elapsed % beat_interval) / beat_interval
            # Sharp pulse on beat (phase 0), then decay
            pulse = math.exp(-5 * beat_phase)
            repulsion = repulsion_min + (repulsion_max - repulsion_min) * pulse

            # Compute and apply forces
            forces = compute_forces(nodes, edges, repulsion, attraction)
            update_positions(base_url, nodes, forces, damping=pulse_cfg.get("damping", 0.1))

            # Wait for next frame
            next_frame = t_start + (int(elapsed / frame_interval) + 1) * frame_interval
            sleep_time = next_frame - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopped.")

    print("Done.")


if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else "../config/pulse.yaml"
    run(config)
