import asyncio
import json
from pathlib import Path
import sys

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from tools.generate_build_db import (
    BuildRequest,
    analyze_indices,
    review_local_database,
    run_harvest,
)


def test_review_local_database_reports_status(tmp_path):
    build_dir = tmp_path / "builds"
    build_dir.mkdir()

    valid_payload = json.loads(
        Path("src/data/builds/alchemist.json").read_text(encoding="utf-8")
    )
    (build_dir / "valid.json").write_text(json.dumps(valid_payload), encoding="utf-8")
    (build_dir / "invalid.json").write_text(
        json.dumps({"build_state": {}}), encoding="utf-8"
    )

    module_dir = tmp_path / "modules"
    module_dir.mkdir()
    module_file = module_dir / "sample.txt"
    module_file.write_text("contenuto", encoding="utf-8")

    module_index_path = tmp_path / "module_index.json"
    module_index_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "module": "sample.txt",
                        "file": str(module_file),
                        "meta": {
                            "name": "sample.txt",
                            "size_bytes": module_file.stat().st_size,
                            "suffix": ".txt",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    output_report = tmp_path / "review.json"
    report = review_local_database(
        build_dir,
        module_dir,
        module_index_path=module_index_path,
        strict=False,
        output_path=output_report,
    )

    assert output_report.is_file()
    assert report["builds"]["total"] == 2
    assert report["builds"]["valid"] == 1
    assert report["builds"]["invalid"] == 1
    assert report["modules"]["valid"] == 1
    assert report["modules"]["invalid"] == 0


async def _run_core_harvest(tmp_path, monkeypatch):
    sheet_payload = {
        "nome": "Alchemist Sample",
        "razza": "Human",
        "classi": [{"nome": "Alchemist", "livelli": 1, "archetipi": []}],
        "statistiche": {
            "Forza": 12,
            "Destrezza": 14,
            "Costituzione": 13,
            "Intelligenza": 16,
            "Saggezza": 10,
            "Carisma": 8,
        },
        "statistiche_chiave": {"PF": 10, "CA": 12},
        "pf_totali": 10,
        "salvezze": {"tempra": 1, "riflessi": 1, "volonta": 1},
        "skills": [{"name": "Perception", "value": 5}],
        "skills_map": {"Perception": 5},
        "skill_points": 1,
        "talenti": ["Alertness"],
        "capacita_classe": ["Bombs"],
        "equipaggiamento": ["Starter kit"],
        "inventario": {"items": ["Potion"]},
        "spell_levels": {"0": [{"name": "Light"}]},
        "magia": {"spells_known": 1},
        "slot_incantesimi": {"1": 2},
        "ac_breakdown": {"totale": 12},
        "BAB": 1,
        "init": 2,
        "speed": 9,
        "iniziativa": 2,
        "velocita": 9,
    }

    sample_payload = {
        "build_state": {
            "class": "Alchemist",
            "race": "Human",
            "archetype": "Base",
            "step_total": 8,
            "step_labels": {f"step_{i}": {} for i in range(8)},
            "statistics": {"forza": 12, "destrezza": 12},
        },
        "benchmark": {"statistics": {"forza": 12}},
        "export": {"sheet_payload": sheet_payload},
        "narrative": {"backstory": "Test narrative"},
        "ledger": {"entries": [{"label": "gold", "value": 10}]},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/modules/minmax_builder.txt":
            return httpx.Response(200, json=sample_payload)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs.setdefault("transport", transport)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr("tools.generate_build_db.httpx.AsyncClient", client_factory)
    monkeypatch.setattr(
        "tools.generate_build_db.validate_with_schema", lambda *args, **kwargs: None
    )

    output_dir = tmp_path / "builds"
    modules_dir = tmp_path / "modules"
    index_path = tmp_path / "build_index.json"
    module_index_path = tmp_path / "module_index.json"

    await run_harvest(
        [BuildRequest(class_name="Alchemist", mode="core")],
        api_url="http://mock.api",
        api_key="mock-key",
        output_dir=output_dir,
        index_path=index_path,
        modules=[],
        modules_output_dir=modules_dir,
        module_index_path=module_index_path,
        concurrency=1,
        max_retries=1,
        spec_path=None,
        discover=False,
        include_filters=[],
        exclude_filters=[],
        strict=False,
        keep_invalid=True,
        require_complete=False,
        skip_health_check=False,
    )

    return output_dir, index_path


def test_run_harvest_smoke(tmp_path, monkeypatch):
    output_dir, index_path = asyncio.run(_run_core_harvest(tmp_path, monkeypatch))

    saved_build = json.loads(
        (output_dir / "alchemist.json").read_text(encoding="utf-8")
    )
    assert saved_build["build_state"]["class"] == "Alchemist"
    rendered_sheet = saved_build["export"]["sheet_payload"].get("sheet_markdown")
    assert rendered_sheet
    assert "Alchemist Sample" in rendered_sheet
    assert "Velocità" in rendered_sheet

    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["entries"], "L'indice delle build non è stato popolato"
    assert index["entries"][0]["status"] == "ok"


def test_analyze_indices_archives_invalid_payloads(tmp_path):
    build_dir = tmp_path / "builds"
    module_dir = tmp_path / "modules"
    build_dir.mkdir()
    module_dir.mkdir()

    valid_build = build_dir / "valid.json"
    invalid_build = build_dir / "invalid.json"
    valid_build.write_text("{}", encoding="utf-8")
    invalid_build.write_text("{""bad"": true}", encoding="utf-8")

    module_file = module_dir / "bad_module.txt"
    module_file.write_text("content", encoding="utf-8")

    build_index_path = tmp_path / "build_index.json"
    build_index_path.write_text(
        json.dumps(
            {
                "entries": [
                    {"status": "ok", "file": str(valid_build)},
                    {
                        "status": "invalid",
                        "file": str(invalid_build),
                        "error": "schema",
                    },
                    {"status": "error", "file": str(build_dir / "missing.json")},
                ]
            }
        ),
        encoding="utf-8",
    )

    module_index_path = tmp_path / "module_index.json"
    module_index_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "module": "bad_module.txt",
                        "status": "invalid",
                        "file": str(module_file),
                        "error": "meta",
                    },
                    {"module": "missing.txt", "status": "error", "file": "missing"},
                ]
            }
        ),
        encoding="utf-8",
    )

    archive_dir = tmp_path / "archive"
    report = analyze_indices(build_index_path, module_index_path, archive_dir=archive_dir)

    assert report["builds"]["invalid"] == 1
    assert report["builds"]["errors"] == 1
    assert report["modules"]["invalid"] == 1
    assert report["modules"]["errors"] == 1
    assert len(report["archived_files"]) == 2
    assert (archive_dir / "builds" / invalid_build.name).is_file()
    assert (archive_dir / "modules" / module_file.name).is_file()
