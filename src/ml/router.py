"""Router /ml (REF-09 v1): POST /ml/transcribe + GET /ml/health.

Contratto output 1:1 con transcriptImportSchema di pathmaster (ADR-C2).
Audio originale in WORM storage (REQ-001). Consenso: gate lato pathmaster
(REQ-002), questo servizio e' un transcodificatore dumb.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.ml.asr import AsrUnavailable, get_asr_engine
from src.ml.storage import save_audio_worm

router = APIRouter(prefix="/ml", tags=["ml"])

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB: sessioni da ore restano fuori v1


def _audio_dir() -> Path:
    """Directory WORM dell'audio (letta a ogni richiesta: i test la variano
    via env; la costante import-time la congelerebbe al primo import)."""
    return Path(os.environ.get(
        "ML_AUDIO_DIR",
        Path(__file__).resolve().parents[1] / "data" / "ml" / "audio"))


@router.get("/health")
def ml_health():
    engine = os.environ.get("ML_ASR_ENGINE", "fake")
    return {"status": "ok", "engine": engine, "scope": "asr-v1"}


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "file vuoto")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"file oltre {MAX_UPLOAD_BYTES} byte (v1)")
    save_audio_worm(data, file.filename or "audio.bin", _audio_dir())
    try:
        engine = get_asr_engine()
        return engine.transcribe(data, file.filename or "audio.bin")
    except AsrUnavailable as exc:
        raise HTTPException(501, str(exc)) from exc
