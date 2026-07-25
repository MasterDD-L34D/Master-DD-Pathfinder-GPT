# REF-09 v1 — Servizio ASR in Taverna Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Primo servizio ML in Taverna (REF-09 v1, spec grill 2026-07-25): trascrizione ASR italiano→testo con timestamp (REQ-003 di pathmaster) via `POST /ml/transcribe`, con faster-whisper come engine opzionale e contratto **identico** a `transcriptImportSchema` di pathmaster (ADR-C2).

**Architecture:** Router `/ml` nella FastAPI Taverna esistente (`src/ml/`), incluso come `rag_router`. Engine astratto con factory env-driven e **guard**: l'app parte anche senza dipendenze ML (501 onesto se manca faster-whisper), pattern già usato per i provider LLM. Audio WORM in `src/data/ml/audio/` (REQ-001, dedup per sha256). Contratto output 1:1 con `transcriptImportSchema` (pathmaster `apps/server/src/lib/transcript-import.ts`): `{language?, segments: [{start, end, text, speaker?, confidence?}]}` (secondi float; `speaker` omesso in v1 — predisposto per diarizzazione futura).

**Tech Stack:** FastAPI, pytest, `faster-whisper` (opzionale, mai richiesta per test/app base). Nessuna dipendenza obbligatoria nuova.

**Vincoli (spec grill 2026-07-25 + PRD):**
- v1 = SOLO ASR. Diarizzazione (REQ-010), voiceprint (REQ-012), purge (REQ-015): fuori scope, documentati come fasi future.
- Consenso (REQ-002): gate lato pathmaster (alla creazione sessione); il servizio è un transcodificatore "dumb", non gestisce consenso.
- Tutti i test e `launch.py test` verdi SENZA faster-whisper installato (engine fake).
- Ownership: Taverna (Kimi). Contratto verso pathmaster: NON cambiarlo unilateralmente (è il loro schema ADR-C2).

---

### Task 1: Engine ASR astratto + fake + factory

**Files:**
- Create: `tooling/Master-DD-Taverna/src/ml/__init__.py`
- Create: `tooling/Master-DD-Taverna/src/ml/asr.py`
- Test: `tooling/Master-DD-Taverna/tests/test_ml_asr.py`

- [ ] **Step 1: Write the failing test**

Creare `tests/test_ml_asr.py`:

```python
"""Test per src/ml/asr.py — engine ASR astratto, fake e factory."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ml.asr import (AsrUnavailable, FakeAsrEngine, TranscriptSegment,
                        get_asr_engine)


def test_fake_engine_returns_contract_shape():
    engine = FakeAsrEngine()
    out = engine.transcribe(b"fake-audio-bytes", filename="clip.ogg")
    assert out["language"] == "it"
    segs = out["segments"]
    assert len(segs) >= 1
    for s in segs:
        assert isinstance(s["start"], float) and isinstance(s["end"], float)
        assert s["end"] >= s["start"]
        assert s["text"].strip()
        if "confidence" in s:
            assert 0.0 <= s["confidence"] <= 1.0
        # v1: nessun speaker (diarizzazione futura)
        assert "speaker" not in s


def test_fake_engine_is_deterministic():
    a = FakeAsrEngine().transcribe(b"abc", filename="a.ogg")
    b = FakeAsrEngine().transcribe(b"abc", filename="a.ogg")
    assert a == b


def test_factory_returns_fake_by_default_without_deps(monkeypatch):
    monkeypatch.delenv("ML_ASR_ENGINE", raising=False)
    engine = get_asr_engine()
    assert isinstance(engine, FakeAsrEngine)


def test_factory_faster_whisper_missing_raises_honest(monkeypatch):
    monkeypatch.setenv("ML_ASR_ENGINE", "faster_whisper")
    # faster-whisper NON e' installato nel venv di test: atteso errore onesto
    try:
        get_asr_engine()
    except AsrUnavailable as exc:
        assert "faster-whisper" in str(exc).lower()
    else:
        raise AssertionError("atteso AsrUnavailable")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tooling/Master-DD-Taverna && .venv/Scripts/python -m pytest tests/test_ml_asr.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.ml'`.

- [ ] **Step 3: Implement `src/ml/__init__.py` e `src/ml/asr.py`**

`src/ml/__init__.py`:

```python
"""Servizi ML di Taverna (REF-09). v1: ASR. Diarizzazione/voiceprint: futuro."""
```

`src/ml/asr.py`:

```python
"""Engine ASR per il servizio /ml/transcribe (REF-09 v1).

Contratto output: `transcriptImportSchema` di pathmaster (ADR-C2):
{"language": str, "segments": [{"start": float, "end": float, "text": str,
"confidence": float?}]} — secondi float, `speaker` omesso in v1 (predisposto
per la diarizzazione futura).

Engine: `faster_whisper` (reale, dipendenza opzionale) | `fake`
(deterministico, per test e sviluppo senza GPU/modello). Factory env-driven:
ML_ASR_ENGINE (default "fake"), ML_ASR_MODEL (default "small"),
ML_ASR_DEVICE (default "auto"), ML_ASR_COMPUTE_TYPE (default "int8").
"""
from __future__ import annotations

import os
from typing import Protocol, TypedDict


class TranscriptSegment(TypedDict, total=False):
    start: float
    end: float
    text: str
    confidence: float


class Transcript(TypedDict, total=False):
    language: str
    segments: list[TranscriptSegment]


class AsrUnavailable(RuntimeError):
    """Engine richiesto ma non disponibile (dipendenza opzionale mancante)."""


class AsrEngine(Protocol):
    def transcribe(self, audio: bytes, filename: str) -> Transcript: ...


class FakeAsrEngine:
    """Engine deterministico: 2 segmenti fissi calati sulla durata stimata."""

    def transcribe(self, audio: bytes, filename: str) -> Transcript:
        dur = max(len(audio) / 16000.0, 1.0)  # stima grezza ~16KB/s
        return {
            "language": "it",
            "segments": [
                {"start": 0.0, "end": round(dur / 2, 3),
                 "text": f"[trascrizione simulata di {filename}, parte 1]",
                 "confidence": 0.99},
                {"start": round(dur / 2, 3), "end": round(dur, 3),
                 "text": f"[trascrizione simulata di {filename}, parte 2]",
                 "confidence": 0.98},
            ],
        }


class FasterWhisperEngine:
    """Engine reale via faster-whisper (import lazy: dipendenza opzionale)."""

    def __init__(self, model: str, device: str, compute_type: str):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise AsrUnavailable(
                "faster-whisper non installato: pip install -r requirements-ml.txt "
                "(o ML_ASR_ENGINE=fake per il mock)") from exc
        self._model = WhisperModel(model, device=device, compute_type=compute_type)

    def transcribe(self, audio: bytes, filename: str) -> Transcript:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix="-" + filename, delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name
        segments_out: list[TranscriptSegment] = []
        segments, info = self._model.transcribe(tmp_path, language="it",
                                                vad_filter=True)
        for seg in segments:
            entry: TranscriptSegment = {
                "start": float(seg.start), "end": float(seg.end),
                "text": seg.text.strip(),
            }
            if seg.avg_logprob is not None:
                # logprob -> confidenza approssimata in [0,1] (clamp)
                entry["confidence"] = max(0.0, min(1.0, 1.0 + seg.avg_logprob))
            segments_out.append(entry)
        if not segments_out:
            raise AsrUnavailable("faster-whisper: nessun segmento prodotto "
                                 "(audio muto o non decodificabile?)")
        return {"language": info.language or "it", "segments": segments_out}


def get_asr_engine() -> AsrEngine:
    kind = os.environ.get("ML_ASR_ENGINE", "fake").strip().lower()
    if kind == "fake":
        return FakeAsrEngine()
    if kind == "faster_whisper":
        return FasterWhisperEngine(
            model=os.environ.get("ML_ASR_MODEL", "small"),
            device=os.environ.get("ML_ASR_DEVICE", "auto"),
            compute_type=os.environ.get("ML_ASR_COMPUTE_TYPE", "int8"))
    raise AsrUnavailable(f"ML_ASR_ENGINE sconosciuto: {kind!r} "
                         "(attesi: fake, faster_whisper)")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_ml_asr.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit** `feat(ml): add asr engine abstraction with fake and factory`

---

### Task 2: Storage WORM + router `/ml`

**Files:**
- Create: `tooling/Master-DD-Taverna/src/ml/storage.py`
- Create: `tooling/Master-DD-Taverna/src/ml/router.py`
- Test: `tooling/Master-DD-Taverna/tests/test_ml_router.py`

- [ ] **Step 1: Write the failing test**

Creare `tests/test_ml_router.py`:

```python
"""Test per src/ml/router.py + storage WORM (REF-09 v1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from src.ml.storage import save_audio_worm


def test_worm_storage_dedup_immutable(tmp_path):
    p1, sha1 = save_audio_worm(b"audio-bytes", "clip.ogg", tmp_path)
    p2, sha2 = save_audio_worm(b"audio-bytes", "clip.ogg", tmp_path)
    assert sha1 == sha2 and p1 == p2
    assert len(list(tmp_path.iterdir())) == 1  # nessuna riscrittura
    p3, sha3 = save_audio_worm(b"altri-bytes", "clip.ogg", tmp_path)
    assert sha3 != sha1 and p3 != p1


def test_transcribe_endpoint_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("ML_ASR_ENGINE", "fake")
    monkeypatch.setenv("ML_AUDIO_DIR", str(tmp_path))
    from src.app import app
    client = TestClient(app)
    resp = client.post("/ml/transcribe",
                       files={"file": ("clip.ogg", b"audio-finto", "audio/ogg")})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["language"] == "it"
    assert len(data["segments"]) >= 1
    seg = data["segments"][0]
    assert {"start", "end", "text"} <= set(seg)
    assert seg["end"] >= seg["start"]
    # WORM: l'audio e' persistito
    assert len(list(tmp_path.iterdir())) == 1


def test_transcribe_engine_unavailable_is_honest_501(monkeypatch, tmp_path):
    monkeypatch.setenv("ML_ASR_ENGINE", "faster_whisper")  # non installato in test
    monkeypatch.setenv("ML_AUDIO_DIR", str(tmp_path))
    from src.app import app
    client = TestClient(app)
    resp = client.post("/ml/transcribe",
                       files={"file": ("clip.ogg", b"audio-finto", "audio/ogg")})
    assert resp.status_code == 501
    assert "faster-whisper" in resp.json()["detail"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_ml_router.py -q`
Expected: FAIL — ModuleNotFoundError `src.ml.storage`.

- [ ] **Step 3: Implement storage e router**

`src/ml/storage.py`:

```python
"""Storage WORM dell'audio originale (REQ-001: immutabile, dedup per sha256)."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path


def save_audio_worm(data: bytes, filename: str, audio_dir: Path) -> tuple[Path, str]:
    """Scrive (una sola volta) l'audio in audio_dir/<sha16>_<nome-sicuro>.

    Stesso contenuto -> stesso path, nessuna riscrittura (WORM).
    Ritorna (path, sha256 esadecimale completo)."""
    sha = hashlib.sha256(data).hexdigest()
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)[:80] or "audio.bin"
    audio_dir.mkdir(parents=True, exist_ok=True)
    path = audio_dir / f"{sha[:16]}_{safe}"
    if not path.exists():
        path.write_bytes(data)
    return path, sha
```

`src/ml/router.py`:

```python
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

ML_AUDIO_DIR = Path(os.environ.get(
    "ML_AUDIO_DIR",
    Path(__file__).resolve().parents[1] / "data" / "ml" / "audio"))

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB: sessioni da ore restano fuori v1


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
    save_audio_worm(data, file.filename or "audio.bin", ML_AUDIO_DIR)
    try:
        engine = get_asr_engine()
        return engine.transcribe(data, file.filename or "audio.bin")
    except AsrUnavailable as exc:
        raise HTTPException(501, str(exc)) from exc
```

Nota: `ML_AUDIO_DIR` letto a import-time; per i test basta `monkeypatch.setenv` PRIMA di importare `src.app` (il test lo fa).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_ml_router.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit** `feat(ml): add worm audio storage and transcribe router`

---

### Task 3: Wiring app + dipendenze opzionali + docs

**Files:**
- Modify: `tooling/Master-DD-Taverna/src/app.py` (include ml_router con guard)
- Create: `tooling/Master-DD-Taverna/requirements-ml.txt`
- Create: `tooling/Master-DD-Taverna/docs/ML_ASR.md`

- [ ] **Step 1: Wiring con guard**

In `src/app.py`, accanto a `app.include_router(rag_router)` (riga ~522):

```python
try:
    from src.ml.router import router as ml_router
    app.include_router(ml_router)
except Exception as exc:  # pragma: no cover - la guardia non deve mai fermare l'app
    import logging
    logging.getLogger(__name__).warning("router /ml non registrato: %s", exc)
```

- [ ] **Step 2: `requirements-ml.txt`**

```text
# Dipendenze OPZIONALI servizi ML (REF-09). L'app base NON le richiede:
# senza installazione, /ml usa l'engine fake o risponde 501 onesto.
faster-whisper>=1.1.0
```

- [ ] **Step 3: `docs/ML_ASR.md`**

Contenuto: scopo (REF-09 v1, solo ASR), contratto (identico a transcriptImportSchema ADR-C2, link al file pathmaster), env vars (`ML_ASR_ENGINE|MODEL|DEVICE|COMPUTE_TYPE`, `ML_AUDIO_DIR`), WORM/REQ-001, consenso lato pathmaster (REQ-002), fuori scope (diarizzazione REQ-010, voiceprint REQ-012, purge REQ-015), smoke manuale con engine reale.

- [ ] **Step 4: Gate**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -m pytest tests/ -q
python launch.py test   # dalla root: deve restare TUTTE LE VERIFICHE OK senza faster-whisper
```

- [ ] **Step 5: Commit** `feat(ml): wire ml router with guard and document asr service`

---

### Task 4: Smoke reale + notifica pathmaster (manuale, quando si vuole GPU/modello)

- [ ] **Step 1: Install opzionale + smoke**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -m pip install -r requirements-ml.txt
ML_ASR_ENGINE=faster_whisper .venv/Scripts/uvicorn src.app:app --port 8000
# altro terminale: curl -F "file=@clip-test.ogg" http://localhost:8000/ml/transcribe
```

Expected: JSON con segmenti reali timestamped in italiano. Registrare nel doc il tempo/modello usato (small/int8 su CPU è il default onesto).

- [ ] **Step 2: Notifica a pathmaster**

Nuovo spec in `pathmaster-dd/docs/superpowers/specs/2026-07-25-ref09-asr-endpoint.md`: endpoint pronto (o pronto al piano), contratto = loro `transcriptImportSchema` (nessuna modifica richiesta al loro import), engine fake default per i test, install opzionale per il reale. Da fare a servizio effettivamente implementato (Task 1-3), non al solo piano.

---

## Self-Review

**Spec coverage:**
- v1 solo ASR, diarizzazione/voiceprint fuori scope → Task 1 (speaker omesso, test dedicato) + docs ✓
- Router `/ml` nella FastAPI esistente con guard dipendenze → Task 2 + Task 3 Step 1 ✓
- Contratto = transcriptImportSchema pathmaster (start/end float sec, text, confidence opt, speaker opt) → Task 1 test di forma + Task 2 test endpoint ✓
- WORM audio (REQ-001) → `save_audio_worm` + test dedup ✓
- Consenso lato pathmaster (REQ-002) → docstring router + docs ✓
- Test verdi senza faster-whisper → engine fake di default + test factory ✓
- Ownership/contratto non unilaterale → notifica pathmaster (Task 4 Step 2), nessuna modifica al loro schema ✓

**Placeholder scan:** il smoke reale (Task 4 Step 1) è manuale per design (download modello ~500MB non automatizzabile in gate); tutto il resto è codice completo. Nessun TBD.

**Type consistency:** `Transcript`/`TranscriptSegment` TypedDict identici tra asr.py e test; `get_asr_engine() -> AsrEngine`; `save_audio_worm(bytes, str, Path) -> tuple[Path, str]`; env vars identiche in asr.py, router.py, test e docs.
