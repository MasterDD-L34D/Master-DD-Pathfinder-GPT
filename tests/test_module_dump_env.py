import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


@pytest.fixture
def configure_settings(monkeypatch: pytest.MonkeyPatch):
    import src.app as app_module
    import src.config as config

    original_env_allow = os.getenv("ALLOW_MODULE_DUMP")
    original_env_api = os.getenv("API_KEY")
    original_settings = app_module.settings

    def _configure(allow_module_dump: str | None):
        monkeypatch.delenv("ALLOW_MODULE_DUMP", raising=False)
        if allow_module_dump is not None:
            monkeypatch.setenv("ALLOW_MODULE_DUMP", allow_module_dump)
        monkeypatch.setenv("API_KEY", "test-api-key")

        new_settings = config.Settings()
        app_module.settings = new_settings
        config.settings = new_settings
        if not hasattr(app_module, "LEDGER_TEXT_MODULES"):
            app_module.LEDGER_TEXT_MODULES = set()
        return app_module

    yield _configure

    if original_env_allow is None:
        monkeypatch.delenv("ALLOW_MODULE_DUMP", raising=False)
    else:
        monkeypatch.setenv("ALLOW_MODULE_DUMP", original_env_allow)
    if original_env_api is None:
        monkeypatch.delenv("API_KEY", raising=False)
    else:
        monkeypatch.setenv("API_KEY", original_env_api)
    app_module.settings = original_settings
    config.settings = original_settings


@pytest.fixture
def client_with_default_dump(configure_settings):
    app_module = configure_settings(None)
    with TestClient(app_module.app) as client:
        yield app_module, client


@pytest.fixture
def client_with_module_dump(configure_settings):
    app_module = configure_settings("true")
    with TestClient(app_module.app) as client:
        yield app_module, client


def test_module_truncated_when_env_missing(client_with_default_dump):
    app_module, client = client_with_default_dump
    headers = {"x-api-key": "test-api-key"}

    response = client.get("/modules/base_profile.txt", headers=headers)

    assert response.status_code == 206
    assert response.headers["X-Content-Partial"] == "true"
    assert response.headers["X-Content-Truncated"] == "true"
    assert "[contenuto troncato" in response.text
    assert "x-truncated=true" in response.text


def test_module_full_body_when_env_enabled(client_with_module_dump):
    app_module, client = client_with_module_dump
    headers = {"x-api-key": "test-api-key"}
    module_path = app_module.MODULES_DIR / "base_profile.txt"
    expected = module_path.read_text(encoding="utf-8")

    response = client.get("/modules/base_profile.txt", headers=headers)

    assert response.status_code == 200
    assert response.text == expected
    assert "X-Content-Partial" not in response.headers
