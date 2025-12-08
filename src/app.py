import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from .config import MODULES_DIR, DATA_DIR, settings

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Perform startup checks using FastAPI lifespan API."""

    _validate_directories(raise_on_error=True)
    yield


app = FastAPI(
    title="Pathfinder 1E Master DD Core API",
    version="1.0.0",
    description="API minimale per esporre i moduli del kernel Master DD a un GPT tramite Actions.",
    lifespan=lifespan,
)


async def require_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    """Validate the provided API key header against settings."""

    if settings.allow_anonymous:
        return

    if settings.api_key is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "API key non configurata. Imposta API_KEY oppure abilita ALLOW_ANONYMOUS=true"
            ),
        )
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _list_files(base: Path) -> List[Dict]:
    out: List[Dict] = []
    if not base.exists() or not base.is_dir():
        raise HTTPException(
            status_code=503,
            detail=f"Directory di configurazione non trovata: {base}",
        )
    for p in sorted(base.iterdir()):
        if p.is_file():
            out.append(
                {
                    "name": p.name,
                    "size_bytes": p.stat().st_size,
                    "suffix": p.suffix,
                }
            )
    return out


@app.get("/health")
async def health() -> Dict[str, str]:
    """Simple healthcheck for Actions."""
    error = _validate_directories()
    if error:
        raise HTTPException(status_code=503, detail=error)

    return {"status": "ok"}


_dir_validation_error: str | None = None


def _validate_directories(raise_on_error: bool = False) -> str | None:
    """Ensure configured module/data directories exist and log issues.

    Parameters
    ----------
    raise_on_error: bool
        If True, a RuntimeError is raised when validation fails.
    """

    global _dir_validation_error

    errors: list[str] = []
    for label, path in ("modules", MODULES_DIR), ("data", DATA_DIR):
        if not path.exists() or not path.is_dir():
            message = f"Directory {label} mancante o non accessibile: {path}"
            logging.error(message)
            errors.append(message)

    if errors:
        _dir_validation_error = "; ".join(errors)
        if raise_on_error:
            raise RuntimeError(_dir_validation_error)
    else:
        _dir_validation_error = None

    return _dir_validation_error


@app.get("/modules", response_model=List[Dict])
async def list_modules(_: None = Depends(require_api_key)) -> List[Dict]:
    """Return the list of available module files (txt/md/json)."""
    return _list_files(MODULES_DIR)


@app.get("/modules/{name:path}/meta")
async def get_module_meta(name: str, _: None = Depends(require_api_key)) -> Dict:
    """Return metadata (no content) for a module file."""
    name_path = Path(name)
    path = (MODULES_DIR / name_path).resolve()
    if not path.is_relative_to(MODULES_DIR):
        raise HTTPException(status_code=400, detail="Invalid module path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Module not found")
    return {
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix,
    }


TEXT_SUFFIXES = {".txt", ".md"}


def _media_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return "text/plain"
    if suffix == ".md":
        return "text/markdown"
    return "text/plain"


@app.api_route("/modules/{name:path}", methods=["GET", "POST"])
async def get_module_content(
    name: str,
    mode: str = Query(default="extended"),
    class_name: str | None = Query(default=None, alias="class"),
    race: str | None = Query(default=None),
    archetype: str | None = Query(default=None),
    stub: bool = Query(default=False, description="Return stub payload for minmax builder"),
    body: Dict | None = Body(default=None),
    _: None = Depends(require_api_key),
):
    """Return the raw text content of a module file or a stubbed builder payload.

    Example names:
    - base_profile.txt
    - Taverna_NPC.txt
    - minmax_builder.txt
    """
    name_path = Path(name)

    stub_requested = stub or str(mode or "").lower() == "stub" or str((body or {}).get("mode", "")).lower() == "stub"

    # Special-case the builder endpoint only when an explicit stub is requested
    if name_path.name == "minmax_builder.txt" and stub_requested:
        resolved_race = race or (body or {}).get("race") or "Human"
        resolved_archetype = (
            archetype
            or (body or {}).get("archetype")
            or (body or {}).get("model")
            or "Base"
        )

        builder_mode = (body or {}).get("builder_mode") or (body or {}).get("mode") or mode
        normalized_mode = "core" if str(builder_mode or "").lower().startswith("core") else "extended"
        step_total = 8 if normalized_mode == "core" else 16
        step_labels = {
            "1": "Profilo Base",
            "2": "Razza & Classe",
            "3": "Archetipi & Multiclasse",
            "4": "Feats & Talenti",
            "5": "Spell & Power Set",
            "6": "Equip & Risorse",
            "7": "Benchmark & Simulazioni",
            "8": "QA & Export",
        }
        if normalized_mode == "extended":
            step_labels.update(
                {
                    "9": "Dummies Sheet",
                    "10": "Esportazione",
                    "11": "Fork/Varianti",
                    "12": "Comparativa",
                    "13": "Meta Rating",
                    "14": "Companion",
                    "15": "Report",
                    "16": "Chiusura",
                }
            )

        base_build_state = {
            "class": class_name or "Unknown",
            "mode": normalized_mode,
            "race": resolved_race,
            "archetype": resolved_archetype,
            "step": 1,
            "step_total": step_total,
            "step_labels": step_labels,
        }

        benchmark = {
            "meta_tier": "T3",
            "ruling_badge": "validated",
            "dpr_snapshot": {
                "livello_1": {"media": 6, "picco": 9},
                "livello_5": {"media": 18, "picco": 26},
            },
        }

        sheet_payload = {
            "classi": [
                {
                    "nome": class_name or "Unknown",
                    "livelli": 1,
                    "archetipi": [resolved_archetype] if resolved_archetype else [],
                }
            ],
            "statistiche": {
                "FOR": 16,
                "DES": 14,
                "COS": 14,
                "INT": 10,
                "SAG": 12,
                "CAR": 8,
            },
            "statistiche_chiave": {
                "attacco": "+4",
                "danni": "1d8+3",
                "ca": 17,
            },
            "benchmarks": {"meta_tier": "T3"},
            "hooks": (body or {}).get("hooks"),
        }

        export_block = {"sheet_payload": sheet_payload}

        base_build_state["statistics"] = sheet_payload["statistiche"]
        benchmark["statistics"] = sheet_payload["statistiche_chiave"]

        narrative = (
            f"{resolved_race or 'Avventuriero'} {resolved_archetype or 'Base'} pronta/o per il campo, "
            f"specializzata/o in tattiche da {class_name or 'classe'}."
        )
        ledger = {
            "movimenti": [
                {"voce": "Equipaggiamento iniziale", "importo": -150},
                {"voce": "Ricompensa missione", "importo": 250},
            ],
            "currency": {"oro": 100, "argento": 25, "rame": 40},
        }

        payload: Dict = {
            "build_state": base_build_state,
            "benchmark": benchmark,
            "export": export_block,
            "narrative": narrative,
            "sheet": sheet_payload,
            "ledger": ledger,
            "class": class_name,
            "mode": normalized_mode,
        }

        payload["composite"] = {
            "build": {
                "build_state": payload["build_state"],
                "benchmark": payload["benchmark"],
                "export": payload["export"],
            },
            "narrative": narrative,
            "sheet": payload["sheet"],
            "ledger": ledger,
        }

        return JSONResponse(payload)

    path = (MODULES_DIR / name_path).resolve()
    if not path.is_relative_to(MODULES_DIR):
        raise HTTPException(status_code=400, detail="Invalid module path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Module not found")
    media_type = _media_type_for_path(path)
    is_text = path.suffix.lower() in TEXT_SUFFIXES

    if not is_text and not settings.allow_module_dump:
        raise HTTPException(status_code=403, detail="Module download not allowed")

    if not is_text and settings.allow_module_dump:
        return FileResponse(path, media_type=media_type, filename=path.name)

    if settings.allow_module_dump:
        return FileResponse(path, media_type=media_type, filename=path.name)

    max_chars = 4000

    def _truncated_text():
        with path.open("r", encoding="utf-8", errors="ignore") as source:
            chunk = source.read(max_chars + 1)
        if len(chunk) > max_chars:
            yield chunk[:max_chars]
            yield "\n\n[contenuto troncato]"
        else:
            yield chunk

    return StreamingResponse(_truncated_text(), media_type=media_type)


@app.get("/knowledge", response_model=List[Dict])
async def list_knowledge(_: None = Depends(require_api_key)) -> List[Dict]:
    """List knowledge PDFs/MD available in /data."""
    return _list_files(DATA_DIR)


@app.get("/knowledge/{name:path}/meta")
async def get_knowledge_meta(name: str, _: None = Depends(require_api_key)) -> Dict:
    """Return metadata for a knowledge file (PDF/MD)."""
    name_path = Path(name)
    path = (DATA_DIR / name_path).resolve()
    if not path.is_relative_to(DATA_DIR):
        raise HTTPException(status_code=400, detail="Invalid knowledge path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Knowledge file not found")
    return {
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix,
    }
