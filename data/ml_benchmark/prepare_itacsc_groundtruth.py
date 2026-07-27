#!/usr/bin/env python3
"""Ground truth DER dalle annotazioni ASR-ItaCSC (Magic Data, MagicHub).

Il TXT ItaCSC e' per-traccia e ha GIA' timestamp + speaker per turno::

    [start_time,end_time]\tspeaker_id\tgender\ttranscript

quindi niente forced alignment: la ground truth e' la conversione diretta
delle annotazioni. Una conversazione = 2 tracce (un wav+txt per speaker,
registrazione mobile individuale); la ground truth del mix mono e' l'unione
dei turni delle due tracce (l'overlap naturale e' gestito dalla griglia di
`src/ml/der.py`, che ammette piu' speaker ref attivi sullo stesso tick).

Righe con speaker_id "0" (eventi non vocali tipo [LAUGHTER], [MUSIC]):
escluse, non sono attivita' di uno speaker. Trascrizioni valide UTF-8.

Uso (lo zip e' in data/ml_benchmark/itacsc/, gitignored)::

    .venv/Scripts/python data/ml_benchmark/prepare_itacsc_groundtruth.py \
        data/ml_benchmark/itacsc/Italian_Conversational_Speech_Corpus.zip \
        A0001_S001 --max-seconds 300 \
        -o data/ml_benchmark/itacsc/ground_truth_A0001_S001.json

Output: JSON nel formato atteso da `data/ml_smoke/eval_der.py`
({"segments": [{"start", "end", "speaker"}]}, speaker = ID reali G0001...).
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

TURN_RE = re.compile(r"^\[(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)\]\t([^\t]+)\t([^\t]*)\t?(.*)$")
NON_SPEECH_SPEAKER = "0"  # eventi [LAUGHTER]/[MUSIC]/... non attribuiti


def parse_turns(txt: str) -> list[dict]:
    """Parse di un TXT ItaCSC: lista di {"start","end","speaker"} (solo
    turni vocali attribuiti; righe non conformi e non-speech saltate)."""
    turns = []
    for line in txt.splitlines():
        line = line.rstrip("\r")
        if not line.startswith("["):
            continue
        m = TURN_RE.match(line)
        if not m:
            continue
        start, end, speaker = float(m.group(1)), float(m.group(2)), m.group(3)
        if speaker == NON_SPEECH_SPEAKER or end <= start:
            continue
        turns.append({"start": start, "end": end, "speaker": speaker})
    return turns


def build_ground_truth(tracks: list[list[dict]],
                       max_seconds: float | None = None) -> dict:
    """Unisce i turni delle tracce di una conversazione; con --max-seconds
    taglia la finestra (drop turni oltre, clamp dell'end al confine)."""
    segments = []
    for turns in tracks:
        for t in turns:
            if max_seconds is not None:
                if t["start"] >= max_seconds:
                    continue
                t = {**t, "end": min(t["end"], max_seconds)}
            segments.append(t)
    segments.sort(key=lambda s: (s["start"], s["end"]))
    return {"segments": segments}


def conversation_txt_names(zf: zipfile.ZipFile, conv: str) -> list[str]:
    """Nomi TXT delle tracce della conversazione (es. A0001_S001 ->
    TXT/A0001_S001_0_G0001.txt, TXT/A0001_S001_0_G0002.txt)."""
    names = sorted(n for n in zf.namelist()
                   if n.startswith(f"TXT/{conv}_0_") and n.endswith(".txt"))
    if not names:
        raise SystemExit(f"nessuna traccia TXT per {conv!r} nello zip")
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("zip_path", type=Path, help="zip ASR-ItaCSC (gitignored)")
    ap.add_argument("conversation", help="es. A0001_S001")
    ap.add_argument("--max-seconds", type=float, default=None,
                    help="taglia la ground truth ai primi N secondi")
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()

    with zipfile.ZipFile(args.zip_path) as zf:
        tracks = [parse_turns(zf.read(n).decode("utf-8"))
                  for n in conversation_txt_names(zf, args.conversation)]
    gt = build_ground_truth(tracks, max_seconds=args.max_seconds)
    if not gt["segments"]:
        raise SystemExit("ground truth vuota: conversazione o finestra errata?")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(gt, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    speakers = sorted({s["speaker"] for s in gt["segments"]})
    print(f"{args.conversation}: {len(gt['segments'])} turni, "
          f"speaker {speakers}"
          + (f", finestra 0-{args.max_seconds:.0f}s" if args.max_seconds else ""))
    print(f"scritto {args.out}")


if __name__ == "__main__":
    main()
