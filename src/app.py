from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict
from pathlib import Path

from .config import MODULES_DIR, DATA_DIR

app = FastAPI(
    title="Pathfinder 1E Master DD Core API",
    version="1.0.0",
    description="API minimale per esporre i moduli del kernel Master DD a un GPT tramite Actions.",
)


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
async def list_modules() -> List[Dict]:
    """Return the list of available module files (txt/md/json)."""
    return _list_files(MODULES_DIR)


@app.get("/modules/{name}", response_class=PlainTextResponse)
async def get_module_content(name: str) -> str:
    """Return the raw text content of a module file.

    Example names:
    - base_profile.txt
    - Taverna_NPC.txt
    - minmax_builder.txt
    """
    path = MODULES_DIR / name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Module not found")
    # In caso tu voglia tagliare per lunghezza, puoi farlo qui
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text


@app.get("/modules/{name}/meta")
async def get_module_meta(name: str) -> Dict:
    """Return metadata (no content) for a module file."""
    path = MODULES_DIR / name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Module not found")
    return {
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix,
    }


@app.get("/knowledge", response_model=List[Dict])
async def list_knowledge() -> List[Dict]:
    """List knowledge PDFs/MD available in /data."""
    return _list_files(DATA_DIR)


@app.get("/knowledge/{name}/meta")
async def get_knowledge_meta(name: str) -> Dict:
    """Return metadata for a knowledge file (PDF/MD)."""
    path = DATA_DIR / name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Knowledge file not found")
    return {
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix,
    }
