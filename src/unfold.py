"""GraphStreamer - Unfold: nodes start collapsed, then move one by one to final position."""

import time
import sys
import json

import requests
import yaml


def get_graph(base_url):
    """Read current graph from Gephi streaming endpoint."""
    try:
        r = requests.get(f"{base_url}?operation=getGraph", timeout=5, stream=True)
        nodes = {}
        edges = {}
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
        return nodes, edges
    except Exception as e:
        print(f"Errore lettura grafo: {e}")
        return {}, {}


def send_positions(base_url, updates):
    """Send position updates to Gephi. updates = {node_id: {x, y}}"""
    payload = {"an": updates}
    try:
        requests.post(f"{base_url}?operation=updateGraph", json=payload, timeout=0.5)
    except requests.RequestException:
        pass


def lerp(a, b, t):
    """Linear interpolation between a and b by factor t (0-1)."""
    return a + (b - a) * t


def run(config_path):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    gephi_cfg = cfg["gephi"]
    unfold_cfg = cfg["unfold"]

    base_url = f"http://{gephi_cfg['host']}:{gephi_cfg['port']}/{gephi_cfg['workspace']}"

    duration = unfold_cfg["duration_seconds"]
    fps = unfold_cfg.get("fps", 30)
    transition_seconds = unfold_cfg.get("transition_seconds", 1.0)

    # Read graph from Gephi (these are the FINAL positions)
    print(f"Reading graph from {base_url}...")
    nodes, edges = get_graph(base_url)

    if not nodes:
        print("Nessun nodo trovato! Carica un grafo in Gephi prima di lanciare.")
        sys.exit(1)

    node_ids = list(nodes.keys())
    n = len(node_ids)
    print(f"Found {n} nodes, {len(edges)} edges.")

    # Save final positions
    final_pos = {}
    for nid in node_ids:
        final_pos[nid] = {
            "x": nodes[nid].get("x", 0),
            "y": nodes[nid].get("y", 0),
        }

    # Compute center (start position for all nodes)
    cx = sum(p["x"] for p in final_pos.values()) / n
    cy = sum(p["y"] for p in final_pos.values()) / n

    # Collapse all nodes to center
    print("Collapsing all nodes to center...")
    collapse = {nid: {"x": cx, "y": cy} for nid in node_ids}
    send_positions(base_url, collapse)
    time.sleep(0.5)

    # Calculate timing: spread node reveals evenly across duration
    # Each node gets: wait → then animate to final position
    reveal_interval = (duration - transition_seconds) / n

    print(f"Unfolding {n} nodes over {duration}s ({reveal_interval:.2f}s between each).")
    print("Press Ctrl+C to stop.")

    frame_interval = 1.0 / fps

    try:
        for i, nid in enumerate(node_ids):
            # Animate this node from center to final position
            t_anim_start = time.perf_counter()

            while True:
                elapsed = time.perf_counter() - t_anim_start
                t = min(elapsed / transition_seconds, 1.0)

                # Ease-out cubic
                t_ease = 1 - (1 - t) ** 3

                x = lerp(cx, final_pos[nid]["x"], t_ease)
                y = lerp(cx, final_pos[nid]["y"], t_ease)

                send_positions(base_url, {nid: {"x": x, "y": y}})

                if t >= 1.0:
                    break

                time.sleep(frame_interval)

            # Wait before next node
            if i < n - 1:
                time.sleep(reveal_interval)

    except KeyboardInterrupt:
        print("\nStopped.")

    print("Done. All nodes in final position.")


if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else "../config/unfold.yaml"
    run(config)
