"""GraphStreamer - Main: plays audio file and streams graph updates to Gephi in sync."""

import time
import sys

import yaml
import numpy as np

from audio_analyzer import analyze_file
from gephi_client import GephiClient


def run(audio_path, config_path="config/mapping.yaml"):
    # Load config
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    gephi_cfg = cfg["gephi"]
    map_cfg = cfg["mapping"]

    client = GephiClient(gephi_cfg["host"], gephi_cfg["port"], gephi_cfg["workspace"])

    # Analyze audio
    print(f"Analyzing: {audio_path}")
    data = analyze_file(audio_path)
    sr = data["sr"]
    hop = data["hop_length"]
    n_frames = data["n_frames"]
    beats_set = set(data["beats"].tolist())
    band_energy = data["band_energy"]

    # Time per frame
    frame_duration = hop / sr

    # Create initial node
    client.update_node("center", label="GraphStreamer", size=10, r=0.3, g=0.3, b=0.3, x=0, y=0)
    print(f"Streaming {n_frames} frames to Gephi ({frame_duration*1000:.1f}ms per frame)...")
    print("Press Ctrl+C to stop.")

    t_start = time.perf_counter()

    try:
        for frame in range(n_frames):
            t_expected = t_start + frame * frame_duration

            # Beat pulse
            is_beat = frame in beats_set
            size = map_cfg["beat"]["size_max"] if is_beat else map_cfg["beat"]["size_min"]

            # Color from frequency bands
            r = float(band_energy["low"][frame]) if frame < len(band_energy["low"]) else 0.1
            g = float(band_energy["mid"][frame]) if frame < len(band_energy["mid"]) else 0.1
            b = float(band_energy["high"][frame]) if frame < len(band_energy["high"]) else 0.1

            client.update_node("center", size=size, r=r, g=g, b=b)

            # Wait to stay in sync
            elapsed = time.perf_counter() - t_start
            sleep_time = (frame + 1) * frame_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopped.")

    # Reset node
    client.update_node("center", size=10, r=0.3, g=0.3, b=0.3)
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <audio_file.wav>")
        sys.exit(1)
    config = sys.argv[2] if len(sys.argv) > 2 else "../config/mapping.yaml"
    run(sys.argv[1], config)
