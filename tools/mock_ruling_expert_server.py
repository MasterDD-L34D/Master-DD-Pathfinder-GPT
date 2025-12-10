"""Lightweight mock Ruling Expert API for local generation runs."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Mock Ruling Expert", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/{path:path}")
async def validate_ruling(payload: dict[str, Any], path: str = "") -> dict[str, Any]:
    build = payload.get("build")
    if not isinstance(build, dict):
        raise HTTPException(status_code=400, detail="Campo 'build' mancante o non valido")

    badge = build.get("ruling_badge") or "full"
    sources = build.get("ruling_sources")
    if not sources:
        sources = ["mock_ruling_expert"]

    return {"ruling_badge": badge, "sources": sources}
