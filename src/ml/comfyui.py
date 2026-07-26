"""Engine ComfyUI (F3, IMG-05): Taverna parla al server ComfyUI locale via
HTTP API (POST /prompt + polling /history + GET /view). ComfyUI resta un
processo separato avviato al bisogno (run_nvidia_gpu.bat): se non risponde,
501 onesto con le istruzioni di avvio — mai un traceback raw.

Config: ML_IMG_COMFY_URL (default http://127.0.0.1:8188),
ML_IMG_COMFY_MODEL (default sdxl; anche suffix engine comfyui-<model>).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from src.ml.comfy_workflows import MODELS, build_workflow
from src.ml.imagine import ImagineUnavailable, _seed_from

DEFAULT_COMFY_URL = "http://127.0.0.1:8188"


class ComfyUIEngine:
    def __init__(self, base_url: str, model: str,
                 timeout_s: int = 600, poll_interval_s: float = 1.0):
        if model not in MODELS:
            raise ImagineUnavailable(
                f"modello ComfyUI sconosciuto: {model!r} (attesi: {', '.join(MODELS)})")
        if not base_url:
            raise ImagineUnavailable(
                "ML_IMG_ENGINE=comfyui richiede ML_IMG_COMFY_URL "
                "(es. http://127.0.0.1:8188)")
        self._base = base_url.rstrip("/")
        self._model = model
        self._timeout_s = timeout_s
        self._poll_s = poll_interval_s
        self.name = f"comfyui-{model}"

    def _json(self, url: str, payload: dict | None = None):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={"content-type": "application/json"} if payload is not None else {},
            method="POST" if payload is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            raise ImagineUnavailable(
                f"ComfyUI non raggiungibile su {self._base} "
                "(avvia: run_nvidia_gpu.bat in ComfyUI_windows_portable)") from exc

    def generate(self, prompt: str, width: int, height: int,
                 seed: int | None) -> dict:
        seed_val = _seed_from(prompt, seed)
        wf = build_workflow(self._model, prompt, width, height, seed_val)
        posted = self._json(f"{self._base}/prompt", {"prompt": wf})
        pid = posted.get("prompt_id")
        if not pid:
            raise ImagineUnavailable(f"ComfyUI: risposta /prompt senza prompt_id: {posted!r}")

        deadline = time.monotonic() + self._timeout_s
        images = None
        while time.monotonic() < deadline:
            hist = self._json(f"{self._base}/history/{pid}")
            entry = hist.get(pid) if isinstance(hist, dict) else None
            if entry and entry.get("outputs"):
                for node_out in entry["outputs"].values():
                    if node_out.get("images"):
                        images = node_out["images"]
                        break
            if images:
                break
            time.sleep(self._poll_s)
        if not images:
            raise ImagineUnavailable(
                f"ComfyUI: timeout dopo {self._timeout_s}s in attesa del risultato")

        img = images[0]
        qs = urllib.parse.urlencode({
            "filename": img["filename"],
            "subfolder": img.get("subfolder", ""),
            "type": img.get("type", "output"),
        })
        try:
            with urllib.request.urlopen(f"{self._base}/view?{qs}", timeout=60) as resp:
                png = resp.read()
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            raise ImagineUnavailable("ComfyUI: impossibile scaricare l'immagine prodotta") from exc
        if not png.startswith(b"\x89PNG"):
            raise ImagineUnavailable("ComfyUI: l'output non e' un PNG")
        return {"png": png, "width": width, "height": height, "engine": self.name}
