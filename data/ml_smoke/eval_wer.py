#!/usr/bin/env python3
"""Mini WER/CER del transcript di smoke E2 contro la ground truth TTS.

Uso: .venv/Scripts/python data/ml_smoke/eval_wer.py
Normalizza (lowercase, solo alfanumerici+spazi) e calcola WER (Levenshtein
sulle parole) e CER (sui caratteri). Strumento una tantum dello smoke
2026-07-26: per la misura formale REQ-003 serve un corpus reale annotato.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-zàèéìòù0-9 ]+", " ", text)
    return " ".join(text.split())


def levenshtein(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[j - 1] + 1,
                            prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


def main():
    gt = normalize((HERE / "ground_truth.txt").read_text(encoding="utf-8"))
    tr = json.loads((HERE / "transcript.json").read_text(encoding="utf-8"))
    hyp = normalize(" ".join(s["text"] for s in tr["segments"]))
    wer = levenshtein(gt.split(), hyp.split()) / max(1, len(gt.split()))
    cer = levenshtein(gt, hyp) / max(1, len(gt))
    print(f"lingua:    {tr['language']}")
    print(f"segmenti:  {len(tr['segments'])}")
    print(f"WER: {wer:.1%}  CER: {cer:.1%}")
    print(f"\nGROUND TRUTH:\n{gt}\n\nIPOTESI:\n{hyp}")


if __name__ == "__main__":
    main()
