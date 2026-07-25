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
