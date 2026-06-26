"""Generate a test WAV file with clear beats and frequency variation."""

import numpy as np
from scipy.io import wavfile

sr = 22050
duration = 30  # seconds
t = np.linspace(0, duration, sr * duration, endpoint=False)

# Kick drum: 80Hz sine pulse every 0.5s (120 BPM)
kick_times = np.arange(0, duration, 0.5)
kick = np.zeros_like(t)
for kt in kick_times:
    mask = (t >= kt) & (t < kt + 0.1)
    kick[mask] += 0.7 * np.sin(2 * np.pi * 80 * (t[mask] - kt)) * np.exp(-30 * (t[mask] - kt))

# Hi-hat: 8000Hz noise burst on off-beats
hihat = np.zeros_like(t)
hihat_times = np.arange(0.25, duration, 0.5)
for ht in hihat_times:
    mask = (t >= ht) & (t < ht + 0.05)
    hihat[mask] += 0.3 * np.random.randn(mask.sum()) * np.exp(-60 * (t[mask] - ht))

# Mid melody: 440Hz sine that comes in at second 10
melody = np.zeros_like(t)
mel_mask = t >= 10
melody[mel_mask] = 0.4 * np.sin(2 * np.pi * 440 * t[mel_mask])
# Amplitude envelope: pulses with the beat
for kt in kick_times:
    if kt >= 10:
        mask = (t >= kt) & (t < kt + 0.3)
        melody[mask] *= np.exp(-5 * (t[mask] - kt))

# Mix
mix = kick + hihat + melody
mix = mix / np.abs(mix).max() * 0.9  # normalize

# Save
wavfile.write("test_audio.wav", sr, (mix * 32767).astype(np.int16))
print(f"Created: test_audio.wav ({duration}s, {sr}Hz, 120 BPM)")
print("- 0-30s: kick drum (80Hz, every beat)")
print("- 0-30s: hi-hat (8kHz, off-beats)")
print("- 10-30s: melody (440Hz, synced to beat)")
