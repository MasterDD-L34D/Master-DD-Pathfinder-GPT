#!/usr/bin/env python3
"""RAG eval A-minima (grill 2026-07-25): question set curato -> hit/miss top-k.

Misura il RETRIEVAL (il documento atteso e' in top-k?), non la generazione.
Riusa il Retriever reale (stesso del RAG in produzione). Rieseguire dopo ogni
reindice/import: e' il regression test del retrieval.

Uso:
    .venv/Scripts/python tools/eval_rag_retrieval.py            # report a video
    .venv/Scripts/python tools/eval_rag_retrieval.py --write    # salva reports/rag_eval_report.json (gitignored? no: committato)
    .venv/Scripts/python tools/eval_rag_retrieval.py --fail-under 0.8   # exit 1 sotto soglia
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

QUESTIONS_PATH = ROOT / "data" / "rag_eval_questions.json"
REPORT_PATH = ROOT / "reports" / "rag_eval_report.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--fail-under", type=float, default=None,
                    help="exit 1 se l'hit rate scende sotto questa soglia (0-1)")
    args = ap.parse_args()

    spec = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    top_k = spec.get("top_k", 5)

    from sentence_transformers import SentenceTransformer
    from src.rag.retriever import Retriever
    from src.rag.store import VectorStore

    store = VectorStore(ROOT / "src" / "data" / "vector_store")
    if not store.is_ready():
        sys.exit("ERRORE: vector store non inizializzato. Esegui tools/index_rag.py")
    encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    retriever = Retriever(store, encoder)

    results = []
    hits = 0
    for q in spec["questions"]:
        expected = q["expected"].lower()
        chunks = retriever.search(q["query"], top_k=top_k)
        found_at = None
        for i, c in enumerate(chunks, 1):
            if expected in c.get("source", "").lower():
                found_at = i
                break
        ok = found_at is not None
        hits += ok
        results.append({"id": q["id"], "query": q["query"], "expected": q["expected"],
                        "hit": ok, "rank": found_at,
                        "top_source": chunks[0].get("source", "") if chunks else ""})
        mark = "OK " if ok else "MISS"
        print(f"[{mark}] #{found_at or '-'} {q['id']}: {q['query']!r} -> {q['expected']}")

    total = len(results)
    rate = hits / total if total else 0.0
    print(f"\nhit rate: {hits}/{total} = {rate:.0%} (top-{top_k})")

    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(
            {"top_k": top_k, "hits": hits, "total": total, "rate": rate,
             "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report: {REPORT_PATH}")

    if args.fail_under is not None and rate < args.fail_under:
        print(f"SOTTO SOGLIA {args.fail_under:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
