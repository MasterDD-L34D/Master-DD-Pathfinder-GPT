"""Storage WORM dell'audio originale (REQ-001: immutabile, dedup per sha256)
e delle immagini generate (F3: content-addressed, write-once)."""
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


def save_image_worm(data: bytes, image_dir: Path) -> tuple[Path, str, str]:
    """Scrive (una sola volta) l'immagine in image_dir/img_<sha16>.png.

    Content-addressed: stesso contenuto -> stesso id, dedup gratis (WORM).
    Ritorna (path, sha256 esadecimale completo, imageId)."""
    sha = hashlib.sha256(data).hexdigest()
    image_id = f"img_{sha[:16]}"
    image_dir.mkdir(parents=True, exist_ok=True)
    path = image_dir / f"{image_id}.png"
    if not path.exists():
        path.write_bytes(data)
    return path, sha, image_id

