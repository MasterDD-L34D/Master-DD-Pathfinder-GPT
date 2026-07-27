"""Misura DER semplificata (E3, REQ-010): attribution error su griglia fine.

Ispirata al DER standard NIST (md-eval), implementazione in casa (~70 righe,
solo stdlib): le etichette ipotesi "S1".."Sn" sono anonime, quindi si cerca il
mapping ottimo ipotesi->reference per forza bruta (n speaker piccolo) prima di
contare gli errori. Semplificazioni documentate rispetto al NIST formale:

- niente collare di tolleranza ai confini segmento (forgiveness collar);
- griglia temporale fissa (default 10 ms) invece di integrazione continua;
- overlap: ogni speaker di reference attivo sul tick contribuisce al
  denominatore (speaker-time), come NIST; per ogni speaker ref attivo senza il
  suo corrispondente ipotesi mappato attivo si conta miss (nessuna ipotesi sul
  tick) o confusion (ipotesi attiva ma speaker sbagliato);
- false alarm: ogni speaker ipotesi attivo il cui mapping non punta a uno
  speaker ref attivo sul tick.

DER = (miss + false_alarm + confusion) / speaker-time reference.

NON e' il gate formale REQ-010: quello richiede audio reale di sessione.
"""
from __future__ import annotations

import itertools
import math

DEFAULT_TICK_SECONDS = 0.01


def _grid(segments, tick, n_ticks):
    """set di speaker attivi per tick (indice = int(start/tick))."""
    grid = [set() for _ in range(n_ticks)]
    for seg in segments:
        a = int(seg["start"] / tick)
        b = int(math.ceil(seg["end"] / tick))
        for i in range(max(a, 0), min(b, n_ticks)):
            grid[i].add(seg["speaker"])
    return grid


def _score(ref_grid, hyp_grid, mapping):
    """Conteggi errore per un mapping ipotesi->reference (None = non mappato)."""
    inv = {v: k for k, v in mapping.items() if v is not None}
    correct = miss = fa = confusion = scored = 0
    for ref_set, hyp_set in zip(ref_grid, hyp_grid):
        scored += len(ref_set)
        for s in ref_set:
            h = inv.get(s)
            if h is not None and h in hyp_set:
                correct += 1
            elif not hyp_set:
                miss += 1
            else:
                confusion += 1
        for h in hyp_set:
            s = mapping.get(h)
            if s is None or s not in ref_set:
                fa += 1
    return correct, miss, fa, confusion, scored


def compute_der(ref_segments, hyp_segments, tick=DEFAULT_TICK_SECONDS):
    """DER fra reference (ground truth) e ipotesi (segmenti con `speaker`).

    ref/hyp: liste di {"start": float, "end": float, "speaker": str}.
    Ritorna dict con der, componenti (miss/false_alarm/confusion/correct in
    tick), scored_seconds (speaker-time reference) e mapping ottimo trovato."""
    if not ref_segments:
        raise ValueError("reference vuota: niente speaker-time da misurare")
    n_ticks = max(1, int(math.ceil(
        max(s["end"] for s in ref_segments + hyp_segments) / tick)))
    ref_grid = _grid(ref_segments, tick, n_ticks)
    hyp_grid = _grid(hyp_segments, tick, n_ticks)
    ref_labels = sorted({s["speaker"] for s in ref_segments})
    hyp_labels = sorted({s["speaker"] for s in hyp_segments})
    best = None
    for choice in itertools.product(ref_labels + [None], repeat=len(hyp_labels)):
        mapping = dict(zip(hyp_labels, choice))
        result = _score(ref_grid, hyp_grid, mapping)
        err = result[1] + result[2] + result[3]
        if best is None or err < best[0]:
            best = (err, mapping, result)
    _, mapping, (correct, miss, fa, confusion, scored) = best
    return {
        "der": (miss + fa + confusion) / max(1, scored),
        "miss": miss,
        "false_alarm": fa,
        "confusion": confusion,
        "correct": correct,
        "scored_seconds": round(scored * tick, 3),
        "tick_seconds": tick,
        "mapping": mapping,
    }
