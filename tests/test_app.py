from urllib.parse import quote

from fastapi.testclient import TestClient

from src.app import app
from src.config import MODULES_DIR, DATA_DIR

client = TestClient(app)


def test_get_module_content_valid_file():
    response = client.get("/modules/base_profile.txt")
    assert response.status_code == 200
    assert "base" in response.text.lower()


def test_get_module_content_path_traversal():
    response = client.get(f"/modules/{quote('../config.py', safe='')}" )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid module path"


def test_get_module_content_not_found():
    response = client.get("/modules/missing_module.txt")
    assert response.status_code == 404
    assert response.json()["detail"] == "Module not found"


def test_get_knowledge_meta_valid_file():
    sample_file = next(DATA_DIR.iterdir())
    response = client.get(f"/knowledge/{quote(sample_file.name)}/meta")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == sample_file.name
    assert payload["size_bytes"] == sample_file.stat().st_size


def test_get_knowledge_meta_path_traversal():
    response = client.get(f"/knowledge/{quote('../config.py', safe='')}/meta")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid knowledge path"
