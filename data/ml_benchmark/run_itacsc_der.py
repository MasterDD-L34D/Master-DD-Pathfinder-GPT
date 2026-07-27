#!/usr/bin/env python3
"""Misura DER della pipeline reale su conversazioni ASR-ItaCSC (REQ-010).

Per ogni conversazione: estrae le 2 tracce wav dallo zip (gitignored),
taglia ai primi --max-seconds, mixa 50/50 in mono 16 kHz (decode via
faster-whisper/PyAV + soundfile, pattern di ml_smoke/gen_overlap_clip.py),
poi engine REALE FasterWhisperEngine (small/cpu/int8, diarize=True) e DER
via src.ml.der.compute_der contro la ground truth delle annotazioni
(prepare_itacsc_groundtruth.py).

Uso::

    .venv/Scripts/python data/ml_benchmark/run_itacsc_der.py \
        [A0001_S001 ...] [--max-seconds 300]

Mix wav, transcript e ground truth JSON restano in
data/ml_benchmark/itacsc/ (gitignored, rigenerabili). Proxy su audio
reale: il gate formale REQ-010 resta audio di sessione di gioco.
"""
import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ml.der import compute_der
from data.ml_benchmark.prepare_itacsc_groundtruth import (
    build_ground_truth, conversation_txt_names, parse_turns)

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "itacsc"
ZIP_PATH = DATA_DIR / "Italian_Conversational_Speech_Corpus.zip"
SR = 16000


def build_mix(zf: zipfile.ZipFile, conv: str, max_seconds: float,
              out_wav: Path) -> None:
    """Estrae le 2 tracce della conversazione, taglia e mixa in mono."""
    import numpy as np
    import soundfile as sf
    from faster_whisper.audio import decode_audio

    tracks = []
    for n in sorted(n for n in zf.namelist()
                    if n.startswith(f"WAV/{conv}_0_") and n.endswith(".wav")):
        with zf.open(n) as fh:
            audio = decode_audio(io.BytesIO(fh.read()), sampling_rate=SR)
        tracks.append(audio[: int(max_seconds * SR)])
    if len(tracks) < 2:
        raise SystemExit(f"attese 2 tracce wav per {conv!r}, "
                         f"trovate {len(tracks)}")
    n = max(len(t) for t in tracks)
    mix = np.zeros(n, dtype=np.float32)
    for t in tracks:
        mix[: len(t)] += t
    mix /= len(tracks)
    mix *= 0.9 / max(1e-6, float(np.max(np.abs(mix))))  # anti-clip
    sf.write(str(out_wav), mix, SR)


def run_conversation(conv: str, max_seconds: float) -> dict:
    from src.ml.asr import FasterWhisperEngine

    out_wav = DATA_DIR / f"{conv}_mix.wav"
    out_transcript = DATA_DIR / f"transcript_{conv}.json"
    with zipfile.ZipFile(ZIP_PATH) as zf:
        if not out_wav.exists():
            build_mix(zf, conv, max_seconds, out_wav)
        tracks = [parse_turns(zf.read(n).decode("utf-8"))
                  for n in conversation_txt_names(zf, conv)]
    gt = build_ground_truth(tracks, max_seconds=max_seconds)

    engine = FasterWhisperEngine(model="small", device="cpu",
                                 compute_type="int8")
    transcript = engine.transcribe(out_wav.read_bytes(), out_wav.name,
                                   diarize=True)
    out_transcript.write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    r = compute_der(gt["segments"], transcript["segments"])
    r["conversation"] = conv
    r["ref_turns"] = len(gt["segments"])
    r["hyp_segments"] = len(transcript["segments"])
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("conversations", nargs="*",
                    default=["A0001_S001", "A0002_S006", "A0003_S001"])
    ap.add_argument("--max-seconds", type=float, default=300.0)
    args = ap.parse_args()
    if not ZIP_PATH.exists():
        raise SystemExit(f"zip dataset mancante: {ZIP_PATH} "
                         "(download MagicHub, vedi data/ml_benchmark/NOTICE.md)")
    results = []
    for conv in args.conversations:
        r = run_conversation(conv, args.max_seconds)
        results.append(r)
        print(f"{conv}: DER {r['der']:.1%} "
              f"(scored {r['scored_seconds']:.1f}s speaker-time, "
              f"miss {r['miss']}, fa {r['false_alarm']}, "
              f"confusion {r['confusion']} tick; mapping {r['mapping']}; "
              f"ref {r['ref_turns']} turni, hyp {r['hyp_segments']} segmenti)",
              flush=True)
    if len(results) > 1:
        mean = sum(r["der"] for r in results) / len(results)
        print(f"media DER su {len(results)} conversazioni: {mean:.1%}")


if __name__ == "__main__":
    main()
