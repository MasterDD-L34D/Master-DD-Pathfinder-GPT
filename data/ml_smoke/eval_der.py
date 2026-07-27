#!/usr/bin/env python3
"""DER del transcript diarizzato di smoke contro la ground truth a intervalli.

Uso: .venv/Scripts/python data/ml_smoke/eval_der.py
     [transcript.json] [ground_truth.json]
Default: transcript_diarize_overlap.json vs ground_truth_overlap.json.
La formula (NIST semplificato, griglia 10 ms, mapping ottimo S1..Sn -> speaker
veri per forza bruta) e' in src/ml/der.py. Strumento di smoke sul sintetico:
il gate formale REQ-010 richiede audio reale di sessione.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ml.der import compute_der

HERE = Path(__file__).resolve().parent


def main():
    hyp_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "transcript_diarize_overlap.json"
    ref_path = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "ground_truth_overlap.json"
    hyp = json.loads(Path(hyp_path).read_text(encoding="utf-8"))["segments"]
    ref = json.loads(Path(ref_path).read_text(encoding="utf-8"))["segments"]
    r = compute_der(ref, hyp)
    print(f"reference:   {ref_path.name} ({len(ref)} intervalli)")
    print(f"ipotesi:     {hyp_path.name} ({len(hyp)} segmenti)")
    print(f"mapping:     {r['mapping']}")
    print(f"scored time: {r['scored_seconds']} s (griglia {r['tick_seconds']} s)")
    print(f"correct:     {r['correct']} tick")
    print(f"miss:        {r['miss']} tick")
    print(f"false alarm: {r['false_alarm']} tick")
    print(f"confusion:   {r['confusion']} tick")
    print(f"DER: {r['der']:.1%}")


if __name__ == "__main__":
    main()
