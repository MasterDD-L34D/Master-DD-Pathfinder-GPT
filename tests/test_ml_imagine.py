"""Test per il servizio img-gen /ml/imagine (F3, contratto img-gen-design)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from src.ml.storage import save_image_worm

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _client(monkeypatch, tmp_path, engine="fake"):
    monkeypatch.setenv("ML_IMG_ENGINE", engine)
    monkeypatch.setenv("ML_IMG_DIR", str(tmp_path))
    from src.app import app
    return TestClient(app)


def test_worm_image_storage_dedup(tmp_path):
    p1, sha1, id1 = save_image_worm(b"png-bytes", tmp_path)
    p2, sha2, id2 = save_image_worm(b"png-bytes", tmp_path)
    assert (sha1, id1, p1) == (sha2, id2, p2)
    assert id1 == f"img_{sha1[:16]}"
    assert len(list(tmp_path.iterdir())) == 1


def test_imagine_fake_engine_contract(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    resp = client.post("/ml/imagine", json={"prompt": "dungeon di pietra", "width": 256, "height": 128})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mimeType"] == "image/png"
    assert (data["width"], data["height"]) == (256, 128)
    assert data["engine"] == "fake"  # il fake si DICHIARA, mai spacciato
    assert data["imageId"] == f"img_{data['sha256'][:16]}"
    # bytes serviti e validi
    got = client.get(f"/ml/imagine/{data['imageId']}")
    assert got.status_code == 200
    assert got.headers["content-type"] == "image/png"
    assert got.content.startswith(PNG_MAGIC)
    # dimensioni decodificate dall'IHDR
    w = int.from_bytes(got.content[16:20], "big")
    h = int.from_bytes(got.content[20:24], "big")
    assert (w, h) == (256, 128)


def test_imagine_fake_is_deterministic(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    r1 = client.post("/ml/imagine", json={"prompt": "bosco", "seed": 42, "width": 64, "height": 64}).json()
    r2 = client.post("/ml/imagine", json={"prompt": "bosco", "seed": 42, "width": 64, "height": 64}).json()
    assert r1["sha256"] == r2["sha256"]
    r3 = client.post("/ml/imagine", json={"prompt": "bosco diverso", "seed": 42, "width": 64, "height": 64}).json()
    assert r3["sha256"] != r1["sha256"]


def test_imagine_engine_off_is_honest_501(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, engine="off")
    resp = client.post("/ml/imagine", json={"prompt": "qualcosa"})
    assert resp.status_code == 501
    assert "ML_IMG_ENGINE" in resp.json()["detail"]


def test_imagine_flux_missing_dep_is_honest_501(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "diffusers", None)  # simula dep assente
    client = _client(monkeypatch, tmp_path, engine="flux")
    resp = client.post("/ml/imagine", json={"prompt": "qualcosa"})
    assert resp.status_code == 501
    assert "diffusers" in resp.json()["detail"].lower()


def test_imagine_api_engine_requires_url(monkeypatch, tmp_path):
    monkeypatch.delenv("ML_IMG_API_URL", raising=False)
    client = _client(monkeypatch, tmp_path, engine="api")
    resp = client.post("/ml/imagine", json={"prompt": "qualcosa"})
    assert resp.status_code == 501
    assert "ML_IMG_API_URL" in resp.json()["detail"]


def test_imagine_engine_override_in_request(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, engine="off")  # env off, ma la request forza fake
    resp = client.post("/ml/imagine", json={"prompt": "override", "engine": "fake", "width": 64, "height": 64})
    assert resp.status_code == 200
    assert resp.json()["engine"] == "fake"


def test_imagine_input_validation(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    assert client.post("/ml/imagine", json={"prompt": ""}).status_code == 422
    assert client.post("/ml/imagine", json={"prompt": "x", "width": 32}).status_code == 422
    assert client.post("/ml/imagine", json={"prompt": "x" * 2001}).status_code == 422


def test_imagine_get_errors(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    assert client.get("/ml/imagine/non-esiste").status_code == 400
    assert client.get("/ml/imagine/img_0000000000000000").status_code == 404
