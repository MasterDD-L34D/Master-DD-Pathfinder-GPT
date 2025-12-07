from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

import src.app as app_module
from src.app import app
from src.config import MODULES_DIR, DATA_DIR, settings

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def setup_api_key():
    original = settings.api_key
    original_allow_anonymous = settings.allow_anonymous
    settings.api_key = "test-api-key"
    settings.allow_anonymous = False
    yield
    settings.api_key = original
    settings.allow_anonymous = original_allow_anonymous


@pytest.fixture
def auth_headers():
    return {"x-api-key": "test-api-key"}


def test_get_module_content_valid_file(client, auth_headers):
    response = client.get("/modules/base_profile.txt", headers=auth_headers)
    assert response.status_code == 200
    assert "base" in response.text.lower()


def test_get_module_content_path_traversal(client, auth_headers):
    response = client.get(f"/modules/{quote('../config.py', safe='')}" , headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid module path"


def test_get_module_content_not_found(client, auth_headers):
    response = client.get("/modules/missing_module.txt", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Module not found"


def test_get_module_meta_valid_file(client, auth_headers):
    sample_file = next(p for p in MODULES_DIR.iterdir() if p.is_file())
    response = client.get(f"/modules/{quote(sample_file.name)}/meta", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == sample_file.name
    assert payload["size_bytes"] == sample_file.stat().st_size
    assert payload["suffix"] == sample_file.suffix


def test_get_module_meta_not_found(client, auth_headers):
    response = client.get("/modules/missing_module.txt/meta", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Module not found"


def test_get_module_meta_path_traversal(client, auth_headers):
    response = client.get(f"/modules/{quote('../config.py', safe='')}/meta", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid module path"


def test_get_knowledge_meta_valid_file(client, auth_headers):
    sample_file = next(DATA_DIR.iterdir())
    response = client.get(f"/knowledge/{quote(sample_file.name)}/meta", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == sample_file.name
    assert payload["size_bytes"] == sample_file.stat().st_size


def test_get_knowledge_meta_path_traversal(client, auth_headers):
    response = client.get(f"/knowledge/{quote('../config.py', safe='')}/meta", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid knowledge path"


def test_missing_api_key_returns_unauthorized(client):
    response = client.get("/modules")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_wrong_api_key_returns_unauthorized(client, auth_headers):
    response = client.get("/modules", headers={"x-api-key": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_correct_api_key_allows_access(client, auth_headers):
    response = client.get("/modules", headers=auth_headers)
    assert response.status_code == 200


def test_knowledge_requires_api_key(client):
    response = client.get("/knowledge")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_knowledge_with_valid_api_key(client, auth_headers):
    response = client.get("/knowledge", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_missing_configured_api_key_is_rejected(client):
    settings.api_key = None
    response = client.get("/modules")
    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "API key non configurata. Imposta API_KEY oppure abilita ALLOW_ANONYMOUS=true"
    )


def test_allow_anonymous_access(client):
    settings.api_key = None
    settings.allow_anonymous = True
    response = client.get("/modules")
    assert response.status_code == 200


def test_modules_directory_missing_returns_error(auth_headers, monkeypatch, tmp_path):
    missing_dir = tmp_path / "missing_modules"
    monkeypatch.setattr(app_module, "MODULES_DIR", missing_dir)

    with TestClient(app) as local_client:
        response = local_client.get("/modules", headers=auth_headers)

    assert response.status_code == 503
    assert str(missing_dir) in response.json()["detail"]


def test_data_directory_missing_returns_error(auth_headers, monkeypatch, tmp_path):
    missing_dir = tmp_path / "missing_data"
    monkeypatch.setattr(app_module, "DATA_DIR", missing_dir)

    with TestClient(app) as local_client:
        response = local_client.get("/knowledge", headers=auth_headers)

    assert response.status_code == 503
    assert str(missing_dir) in response.json()["detail"]
