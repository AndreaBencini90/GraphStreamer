"""Audio analysis - beat detection and frequency band energy extraction."""

import numpy as np
import librosa


def analyze_file(filepath, hop_length=512):
    """Analyze audio file, return per-frame features."""
    y, sr = librosa.load(filepath, sr=22050, mono=True)

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    S = np.abs(librosa.stft(y, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr)

    band_energy = {
        "low": S[(freqs >= 20) & (freqs < 300)].mean(axis=0),
        "mid": S[(freqs >= 300) & (freqs < 2000)].mean(axis=0),
        "high": S[(freqs >= 2000) & (freqs <= 16000)].mean(axis=0),
    }

    for key in band_energy:
        mx = band_energy[key].max()
        if mx > 0:
            band_energy[key] = band_energy[key] / mx

    return {
        "sr": sr,
        "hop_length": hop_length,
        "beats": beat_frames,
        "onset_env": onset_env,
        "band_energy": band_energy,
        "n_frames": S.shape[1],
    }
