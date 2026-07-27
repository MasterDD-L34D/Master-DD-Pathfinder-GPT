#!/usr/bin/env python3
"""Genera clip_overlap.wav: clip_a (voce Diego) + clip_b (voce Elsa) mixate con
overlap artificiale di 3,0 s nella parte centrale + rumore bianco leggero.

Uso: .venv/Scripts/python data/ml_smoke/gen_overlap_clip.py
Decodifica via faster-whisper (PyAV, niente ffmpeg di sistema), mix numpy,
scrittura wav 16 kHz mono via soundfile. Riproducibile (seed fisso): l'audio
wav e' gitignored, la ground truth (intervalli di presenza delle due clip nel
mix) e' committata in ground_truth_overlap.json. NOTA: la ground truth marca
la *presenza della clip* nel mix, non l'attivita' vocale esatta (le code di
silenzio TTS sono brevi ma non nulle) — approssimazione dichiarata dello
smoke, un motivo in piu' per cui questa misura NON e' il gate REQ-010.
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper.audio import decode_audio

HERE = Path(__file__).resolve().parent
SR = 16000
OVERLAP_SECONDS = 3.0
B_GAIN = 0.9          # voce B leggermente piu' bassa nel mix
NOISE_AMPLITUDE = 0.003  # rumore bianco leggero (~ -50 dBFS)
SEED = 42


def main():
    a = decode_audio(str(HERE / "clip_a.mp3"), sampling_rate=SR)
    b = decode_audio(str(HERE / "clip_b.mp3"), sampling_rate=SR)
    dur_a = len(a) / SR
    start_b = dur_a - OVERLAP_SECONDS
    total = start_b + len(b) / SR
    mix = np.zeros(int(total * SR), dtype=np.float32)
    mix[:len(a)] += a
    off = int(start_b * SR)
    mix[off:off + len(b)] += B_GAIN * b
    rng = np.random.default_rng(SEED)
    mix += (NOISE_AMPLITUDE * rng.standard_normal(len(mix))).astype(np.float32)
    mix *= 0.9 / max(1e-6, float(np.max(np.abs(mix))))  # anti-clip
    sf.write(str(HERE / "clip_overlap.wav"), mix, SR)
    gt = {
        "nota": ("intervalli di PRESENZA delle clip nel mix "
                 "(voce A = it-IT-DiegoNeural, voce B = it-IT-ElsaNeural), "
                 "non attivita' vocale esatta"),
        "overlap_seconds": OVERLAP_SECONDS,
        "b_gain": B_GAIN,
        "noise_amplitude": NOISE_AMPLITUDE,
        "segments": [
            {"start": 0.0, "end": round(dur_a, 2), "speaker": "A"},
            {"start": round(start_b, 2), "end": round(total, 2), "speaker": "B"},
        ],
    }
    (HERE / "ground_truth_overlap.json").write_text(
        json.dumps(gt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"clip_overlap.wav: {total:.2f} s (A 0-{dur_a:.2f}, "
          f"B {start_b:.2f}-{total:.2f}, overlap {OVERLAP_SECONDS} s)")


if __name__ == "__main__":
    main()
