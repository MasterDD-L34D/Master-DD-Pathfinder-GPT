from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.app import app
from src.config import MODULES_DIR, DATA_DIR, settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_api_key():
    original = settings.api_key
    settings.api_key = "test-api-key"
    yield
    settings.api_key = original


@pytest.fixture
def auth_headers():
    return {"x-api-key": "test-api-key"}


def test_get_module_content_valid_file(auth_headers):
    response = client.get("/modules/base_profile.txt", headers=auth_headers)
    assert response.status_code == 200
    assert "base" in response.text.lower()


def test_get_module_content_path_traversal(auth_headers):
    response = client.get(f"/modules/{quote('../config.py', safe='')}" , headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid module path"


def test_get_module_content_not_found(auth_headers):
    response = client.get("/modules/missing_module.txt", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Module not found"


def test_get_knowledge_meta_valid_file(auth_headers):
    sample_file = next(DATA_DIR.iterdir())
    response = client.get(f"/knowledge/{quote(sample_file.name)}/meta", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == sample_file.name
    assert payload["size_bytes"] == sample_file.stat().st_size


def test_get_knowledge_meta_path_traversal(auth_headers):
    response = client.get(f"/knowledge/{quote('../config.py', safe='')}/meta", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid knowledge path"


def test_missing_api_key_returns_unauthorized():
    response = client.get("/modules")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_wrong_api_key_returns_unauthorized(auth_headers):
    response = client.get("/modules", headers={"x-api-key": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_correct_api_key_allows_access(auth_headers):
    response = client.get("/modules", headers=auth_headers)
    assert response.status_code == 200
