from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict
from pathlib import Path

from .config import MODULES_DIR, DATA_DIR, settings

app = FastAPI(
    title="Pathfinder 1E Master DD Core API",
    version="1.0.0",
    description="API minimale per esporre i moduli del kernel Master DD a un GPT tramite Actions.",
)


async def require_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    """Validate the provided API key header against settings."""

    if settings.api_key is None:
        # Se non configurata, non forziamo l'autenticazione.
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _list_files(base: Path) -> List[Dict]:
    out: List[Dict] = []
    if not base.exists():
        return out
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
    return {"status": "ok"}


@app.get("/modules", response_model=List[Dict])
async def list_modules(_: None = Depends(require_api_key)) -> List[Dict]:
    """Return the list of available module files (txt/md/json)."""
    return _list_files(MODULES_DIR)


@app.get("/modules/{name:path}", response_class=PlainTextResponse)
async def get_module_content(name: str, _: None = Depends(require_api_key)) -> str:
    """Return the raw text content of a module file.

    Example names:
    - base_profile.txt
    - Taverna_NPC.txt
    - minmax_builder.txt
    """
    name_path = Path(name)
    path = (MODULES_DIR / name_path).resolve()
    if not path.is_relative_to(MODULES_DIR):
        raise HTTPException(status_code=400, detail="Invalid module path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Module not found")
    # In caso tu voglia tagliare per lunghezza, puoi farlo qui
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text


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
