from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

import src.app as app_module
from src.app import app
from src.config import MODULES_DIR, DATA_DIR, settings
from tools.generate_build_db import schema_for_mode, validate_with_schema

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def disable_module_dump():
    original = settings.allow_module_dump
    settings.allow_module_dump = False
    yield
    settings.allow_module_dump = original


@pytest.fixture
def missing_modules_dir(monkeypatch, tmp_path):
    missing_dir = tmp_path / "missing_modules"
    monkeypatch.setattr(app_module, "MODULES_DIR", missing_dir)
    return missing_dir


@pytest.fixture
def missing_data_dir(monkeypatch, tmp_path):
    missing_dir = tmp_path / "missing_data"
    monkeypatch.setattr(app_module, "DATA_DIR", missing_dir)
    return missing_dir


@pytest.fixture
def data_dir_file(monkeypatch, tmp_path):
    data_file = tmp_path / "data_file"
    data_file.write_text("not a directory")
    monkeypatch.setattr(app_module, "DATA_DIR", data_file)
    return data_file


@pytest.fixture
def temp_data_dir(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(app_module, "DATA_DIR", data_dir)
    return data_dir


@pytest.fixture
def allow_missing_directories(monkeypatch):
    def fake_validate(raise_on_error: bool = False):
        directories = {}
        errors = []
        for label, path in ("modules", app_module.MODULES_DIR), ("data", app_module.DATA_DIR):
            is_valid = path.exists() and path.is_dir()
            message = None
            if not is_valid:
                message = f"Directory {label} mancante o non accessibile: {path}"
                errors.append(message)
            directories[label] = {
                "status": "ok" if is_valid else "error",
                "path": str(path),
                "message": message,
            }

        diagnostic = {"status": "ok" if not errors else "error", "directories": directories}
        if errors:
            diagnostic["errors"] = errors

        app_module._dir_validation_error = "; ".join(errors) if errors else None
        return diagnostic

    monkeypatch.setattr(app_module, "_validate_directories", fake_validate)
    return fake_validate


@pytest.fixture(autouse=True)
def reset_backoff_state():
    app_module._reset_failed_attempts()
    yield
    app_module._reset_failed_attempts()


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
def short_backoff(monkeypatch):
    original_threshold = settings.auth_backoff_threshold
    original_seconds = settings.auth_backoff_seconds
    settings.auth_backoff_threshold = 2
    settings.auth_backoff_seconds = 30
    yield
    settings.auth_backoff_threshold = original_threshold
    settings.auth_backoff_seconds = original_seconds


@pytest.fixture
def auth_headers():
    return {"x-api-key": "test-api-key"}


def test_get_module_content_valid_file(client, auth_headers):
    response = client.get("/modules/base_profile.txt", headers=auth_headers)
    assert response.status_code == 200
    assert "base" in response.text.lower()


def test_get_module_content_sets_text_content_type(client, auth_headers):
    response = client.get("/modules/base_profile.txt", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_minmax_builder_returns_file_content_by_default(client, auth_headers):
    response = client.get("/modules/minmax_builder.txt", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "MinMax Builder" in response.text
    assert response.text.lstrip().startswith("module_name")


def test_minmax_builder_stub_is_opt_in(client, auth_headers):
    response = client.get("/modules/minmax_builder.txt?mode=stub", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    payload = response.json()
    assert payload["build_state"]["mode"] in {"core", "extended"}
    assert payload["sheet"]["classi"][0]["nome"] == "Unknown"


def test_minmax_builder_stub_contains_full_payload(client, auth_headers):
    response = client.get("/modules/minmax_builder.txt?mode=stub", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()

    expected_keys = {
        "build_state",
        "benchmark",
        "export",
        "narrative",
        "sheet",
        "ledger",
        "class",
        "mode",
        "composite",
    }
    assert set(payload.keys()) == expected_keys
    assert "sheet_payload" in payload["export"]
    assert payload["ledger"]["currency"]["oro"] >= 0
    assert payload["composite"]["build"]["export"]["sheet_payload"]


def test_minmax_builder_stub_payload_matches_schema(client, auth_headers):
    response = client.get("/modules/minmax_builder.txt?mode=stub", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()

    schema_filename = schema_for_mode(payload.get("mode", ""))
    validate_with_schema(
        schema_filename,
        payload,
        "test_minmax_builder_stub",
        strict=True,
    )


def test_get_module_content_path_traversal(client, auth_headers):
    response = client.get(f"/modules/{quote('../config.py', safe='')}" , headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid module path"


def test_get_module_content_not_found(client, auth_headers):
    response = client.get("/modules/missing_module.txt", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Module not found"


def test_get_module_content_binary_streamed_without_text_property(
    client, auth_headers
):
    binary_path = MODULES_DIR / "binary_test.bin"
    binary_path.write_bytes(b"\x00\x01" * 2048)

    try:
        with client.stream(
            "GET", "/modules/binary_test.bin", headers=auth_headers
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/plain")
            assert response.is_stream_consumed is False
    finally:
        binary_path.unlink(missing_ok=True)


def test_get_module_content_binary_blocked_when_dump_disabled(
    client, auth_headers, disable_module_dump
):
    binary_path = MODULES_DIR / "binary_blocked.bin"
    binary_path.write_bytes(b"binary-content")

    try:
        response = client.get("/modules/binary_blocked.bin", headers=auth_headers)
        assert response.status_code == 403
        payload = response.json()
        assert payload["detail"] == "Module download not allowed"
        assert "contenuto troncato" not in response.text
    finally:
        binary_path.unlink(missing_ok=True)


def test_text_module_truncated_when_dump_disabled(client, auth_headers, disable_module_dump):
    large_module = MODULES_DIR / "large_module.txt"
    large_module.write_text("A" * 5001)

    try:
        response = client.get("/modules/large_module.txt", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text.endswith("[contenuto troncato]")
        assert "A" * 10 in response.text
    finally:
        large_module.unlink(missing_ok=True)


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


@pytest.mark.parametrize(
    "data_fixture",
    ["missing_data_dir", "data_dir_file"],
)
def test_list_knowledge_returns_503_for_invalid_data_dir(
    client, auth_headers, allow_missing_directories, request, data_fixture
):
    invalid_path = request.getfixturevalue(data_fixture)

    response = client.get("/knowledge", headers=auth_headers)

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == f"Directory di configurazione non trovata: {invalid_path}"
    )


def test_get_knowledge_meta_returns_404_for_traversal_inside_data_dir(
    client, auth_headers, temp_data_dir
):
    traversal_target = f"../{temp_data_dir.name}/ghost.md"
    encoded_target = quote(traversal_target, safe="")

    response = client.get(f"/knowledge/{encoded_target}/meta", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge file not found"


def test_get_module_meta_path_traversal(client, auth_headers):
    response = client.get(f"/modules/{quote('../config.py', safe='')}/meta", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid module path"


def test_get_knowledge_meta_valid_file(client, auth_headers):
    sample_file = next(p for p in DATA_DIR.iterdir() if p.is_file())
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


def test_repeated_wrong_api_key_triggers_backoff(client, short_backoff):
    first_response = client.get("/modules", headers={"x-api-key": "wrong"})
    assert first_response.status_code == 401

    blocked_response = client.get("/modules", headers={"x-api-key": "wrong"})
    assert blocked_response.status_code == 429
    assert "Troppi tentativi" in blocked_response.json()["detail"]
    assert blocked_response.headers.get("Retry-After") == str(
        settings.auth_backoff_seconds
    )

    still_blocked = client.get("/modules", headers={"x-api-key": "wrong"})
    assert still_blocked.status_code == 429


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


def test_modules_directory_missing_returns_error(
    auth_headers, missing_modules_dir, allow_missing_directories
):
    with TestClient(app) as local_client:
        response = local_client.get("/modules", headers=auth_headers)

    assert response.status_code == 503
    assert str(missing_modules_dir) in response.json()["detail"]


def test_data_directory_missing_returns_error(
    auth_headers, missing_data_dir, allow_missing_directories
):
    with TestClient(app) as local_client:
        response = local_client.get("/knowledge", headers=auth_headers)

    assert response.status_code == 503
    assert str(missing_data_dir) in response.json()["detail"]


def test_health_reports_missing_directories(monkeypatch, tmp_path):
    missing_dir = tmp_path / "missing_anything"

    with TestClient(app) as local_client:
        monkeypatch.setattr(app_module, "MODULES_DIR", missing_dir)
        monkeypatch.setattr(app_module, "DATA_DIR", missing_dir)

        response = local_client.get("/health")

    payload = response.json()
    assert response.status_code == 503
    assert payload["status"] == "error"
    assert payload["directories"]["modules"]["status"] == "error"
    assert payload["directories"]["data"]["status"] == "error"
    assert any("mancante" in msg for msg in payload["errors"])


def test_health_reports_valid_directories(client):
    response = client.get("/health")

    payload = response.json()
    assert response.status_code == 200
    assert payload == {
        "status": "ok",
        "directories": {
            "modules": {
                "status": "ok",
                "path": str(MODULES_DIR),
                "message": None,
            },
            "data": {
                "status": "ok",
                "path": str(DATA_DIR),
                "message": None,
            },
        },
    }
