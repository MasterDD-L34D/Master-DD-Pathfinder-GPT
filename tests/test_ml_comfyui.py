"""Test per l'engine ComfyUI (F3, IMG-05): workflow builder + client HTTP."""
import io
import json
import sys
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.ml.comfy_workflows import build_workflow, MODELS
from src.ml.comfyui import ComfyUIEngine
from src.ml.imagine import ImagineUnavailable, get_imagine_engine


class FakeResp:
    def __init__(self, payload, binary=False):
        self._payload = payload
        self._binary = binary

    def read(self):
        return self._payload if self._binary else json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_workflow_sdxl_structure():
    wf = build_workflow("sdxl", "un dungeon", 512, 768, 42)
    # nodi chiave del grafico SDXL minimo
    assert wf["1"]["class_type"] == "CheckpointLoaderSimple"
    assert wf["1"]["inputs"]["ckpt_name"] == "sd_xl_base_1.0.safetensors"
    assert wf["2"]["inputs"]["text"] == "un dungeon"          # prompt positivo
    assert wf["4"]["inputs"]["width"] == 512
    assert wf["4"]["inputs"]["height"] == 768
    assert wf["5"]["class_type"] == "KSampler"
    assert wf["5"]["inputs"]["seed"] == 42
    assert wf["7"]["class_type"] == "SaveImage"


def test_workflow_unknown_model():
    with pytest.raises(ImagineUnavailable, match="workflow"):
        build_workflow("xyz", "p", 64, 64, 1)


def test_engine_generate_success(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=0):
        url = req.full_url if hasattr(req, "full_url") else req
        calls.append(url)
        if url.endswith("/prompt"):
            return FakeResp({"prompt_id": "pid-1"})
        if "/history/" in url:
            return FakeResp({"pid-1": {"outputs": {"7": {"images": [
                {"filename": "taverna_img_00001_.png", "subfolder": "", "type": "output"}]}}}})
        if "/view" in url:
            return FakeResp(b"\x89PNG\r\n\x1a\nfakepng", binary=True)
        raise AssertionError(url)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    engine = ComfyUIEngine("http://127.0.0.1:8188", "sdxl")
    out = engine.generate("un dungeon", 512, 768, 42)
    assert out["png"].startswith(b"\x89PNG")
    assert (out["width"], out["height"]) == (512, 768)
    assert out["engine"] == "comfyui-sdxl"


def test_engine_unreachable_is_honest(monkeypatch):
    def boom(req, timeout=0):
        raise URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    engine = ComfyUIEngine("http://127.0.0.1:8188", "sdxl")
    with pytest.raises(ImagineUnavailable, match="run_nvidia_gpu"):
        engine.generate("p", 64, 64, 1)


def test_engine_poll_timeout(monkeypatch):
    def fake_urlopen(req, timeout=0):
        url = req.full_url if hasattr(req, "full_url") else req
        if url.endswith("/prompt"):
            return FakeResp({"prompt_id": "pid-9"})
        if "/history/" in url:
            return FakeResp({})  # mai pronto
        raise AssertionError(url)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    engine = ComfyUIEngine("http://127.0.0.1:8188", "sdxl", timeout_s=0, poll_interval_s=0)
    with pytest.raises(ImagineUnavailable, match="timeout"):
        engine.generate("p", 64, 64, 1)


def test_factory_comfyui_variants(monkeypatch):
    monkeypatch.setenv("ML_IMG_COMFY_URL", "http://127.0.0.1:8188")
    assert get_imagine_engine("comfyui").name == "comfyui-sdxl"  # default modello
    assert get_imagine_engine("comfyui-flux").name == "comfyui-flux"
    assert get_imagine_engine("comfyui-qwen").name == "comfyui-qwen"
    with pytest.raises(ImagineUnavailable, match="sconosciuto"):
        get_imagine_engine("comfyui-xyz")
