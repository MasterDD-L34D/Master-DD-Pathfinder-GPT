#!/usr/bin/env python3
"""RAG eval — valutazione GENERAZIONE (2026-07-25, punto 8 coda).

Per ogni domanda del question set: retrieval reale (retriever di produzione,
con query-translation integrata) -> generazione col provider configurato
(default: RAG_LLM_PROVIDER da .env) -> rubriche deterministiche
(`expect_all` = tutte le stringhe presenti; `expect_any` = almeno una).

Misura la qualita' della risposta finale del Master in italiano. NON usa
LLM-judge (decisione grill: rubriche deterministiche ora, giudice in futuro).

Uso:
    .venv/Scripts/python tools/eval_rag_generation.py              # report a video
    .venv/Scripts/python tools/eval_rag_generation.py --write      # salva reports/rag_generation_report.json
    .venv/Scripts/python tools/eval_rag_generation.py --only feat-power-attack,equip-chainmail
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

QUESTIONS_PATH = ROOT / "data" / "rag_eval_questions.json"
REPORT_PATH = ROOT / "reports" / "rag_generation_report.json"


def _check(answer: str, q: dict) -> tuple[bool, list[str]]:
    low = answer.lower()
    missing = [s for s in q.get("expect_all", []) if s.lower() not in low]
    any_terms = q.get("expect_any", [])
    any_ok = not any_terms or any(t.lower() in low for t in any_terms)
    ok = not missing and any_ok
    if not any_ok:
        missing.append(f"(nessuna di {any_terms})")
    return ok, missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--only", help="id separati da virgola da valutare (debug)")
    ap.add_argument("--provider", help="override provider (default: env RAG_LLM_PROVIDER)")
    args = ap.parse_args()

    spec = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    top_k = spec.get("top_k", 5)
    only = set(args.only.split(",")) if args.only else None

    from sentence_transformers import SentenceTransformer
    from src.rag.generator import get_provider
    from src.rag.retriever import Retriever
    from src.rag.store import VectorStore

    store = VectorStore(ROOT / "src" / "data" / "vector_store")
    if not store.is_ready():
        sys.exit("ERRORE: vector store non inizializzato")
    retriever = Retriever(store, SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2"))
    provider = get_provider(args.provider)
    print(f"provider: {type(provider).__name__} ({getattr(provider, 'model', 'n/a')})")

    results = []
    hits = 0
    for q in spec["questions"]:
        if only and q["id"] not in only:
            continue
        t0 = time.time()
        chunks = retriever.search(q["query"], top_k=top_k)
        answer = provider.generate(q["query"], chunks)
        ok, missing = _check(answer, q)
        hits += ok
        elapsed = time.time() - t0
        results.append({"id": q["id"], "ok": ok, "missing": missing,
                        "answer_head": answer[:200], "seconds": round(elapsed, 1)})
        mark = "OK " if ok else "MISS"
        print(f"[{mark}] {q['id']} ({elapsed:.0f}s)" + ("" if ok else f" manca: {missing}"))

    total = len(results)
    rate = hits / total if total else 0.0
    print(f"\ngeneration hit rate: {hits}/{total} = {rate:.0%}")

    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(
            {"provider": type(provider).__name__, "model": getattr(provider, "model", None),
             "hits": hits, "total": total, "rate": rate, "results": results},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
