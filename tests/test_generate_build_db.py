import asyncio
import copy
import json
from pathlib import Path
import sys

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from tools.generate_build_db import (
    BuildRequest,
    _enrich_sheet_payload,
    analyze_indices,
    review_local_database,
    run_harvest,
)


def _make_sample_payload() -> dict:
    sheet_payload = {
        "nome": "Alchemist Sample",
        "razza": "Human",
        "classi": [{"nome": "Alchemist", "livelli": 1, "archetipi": []}],
        "statistiche": {
            "FOR": 12,
            "DES": 14,
            "COS": 13,
            "INT": 16,
            "SAG": 10,
            "CAR": 8,
        },
        "statistiche_chiave": {"PF": 10, "CA": 12},
        "pf_totali": 10,
        "salvezze": {},
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
        "ac_breakdown": {},
    }

    return {
        "build_state": {
            "class": "Alchemist",
            "race": "Human",
            "archetype": "Base",
            "step_total": 8,
            "step_labels": {f"step_{i}": {} for i in range(8)},
            "statistics": {"forza": 12, "destrezza": 12},
            "bab": 3,
            "initiative": 4,
            "speed": 9,
            "ac": {
                "AC_base": 10,
                "AC_arm": 4,
                "AC_des": 2,
                "AC_tot": 17,
            },
            "saves": {"Tempra": 5, "Riflessi": 2, "Volontà": 1},
        },
        "benchmark": {"statistics": {"forza": 12}},
        "export": {"sheet_payload": sheet_payload},
        "narrative": {"backstory": "Test narrative"},
        "ledger": {"entries": [{"label": "gold", "value": 10}]},
        "progressione": [
            {"livello": level, "privilegi": [f"Feature {level}"]}
            for level in range(1, 11)
        ],
    }


def test_review_local_database_reports_status(tmp_path):
    build_dir = tmp_path / "builds"
    build_dir.mkdir()

    valid_payload = json.loads(
        Path("src/data/builds/fighter.json").read_text(encoding="utf-8")
    )
    (build_dir / "valid.json").write_text(json.dumps(valid_payload), encoding="utf-8")
    completeness_payload = dict(valid_payload)
    completeness_payload["completeness"] = {"errors": ["Statistiche mancanti"]}
    (build_dir / "incomplete.json").write_text(
        json.dumps(completeness_payload), encoding="utf-8"
    )
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
    assert report["builds"]["total"] == 3
    assert report["builds"]["valid"] == 1
    assert report["builds"]["invalid"] == 2
    assert report["modules"]["valid"] == 1
    assert report["modules"]["invalid"] == 0


def test_review_local_database_flags_missing_progression(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "tools.generate_build_db.validate_with_schema", lambda *args, **kwargs: None
    )

    build_dir = tmp_path / "builds"
    module_dir = tmp_path / "modules"
    build_dir.mkdir()
    module_dir.mkdir()

    sheet_payload = {
        "nome": "Rogue Snapshot",
        "pf_totali": 25,
        "salvezze": {"Tempra": 4},
        "skills_map": {"Percezione": 10},
        "skills": [{"nome": "Percezione", "mod": 10}],
        "equipaggiamento": ["Dagger"],
        "spell_levels": [{"livello": 0, "incantesimi": ["Light"]}],
        "ac_breakdown": {"totale": 17},
        "iniziativa": 3,
        "velocita": 9,
        "skill_points": 0,
        "progressione": [
            {"livello": 1, "privilegi": ["Sneak Attack"]},
        ],
    }

    payload = {
        "class": "Rogue",
        "mode": "core",
        "build_state": {"class": "Rogue"},
        "export": {"sheet_payload": sheet_payload},
        "completeness": {"errors": []},
        "request": BuildRequest(class_name="Rogue", level=5).metadata(),
    }

    (build_dir / "rogue_lvl05.json").write_text(json.dumps(payload), encoding="utf-8")

    report = review_local_database(build_dir, module_dir, strict=False)

    entry = report["builds"]["entries"][0]
    assert entry["status"] == "invalid"
    assert any(
        "Progressione assente al livello 2" in error
        for error in entry.get("completeness_errors", [])
    )


def test_enrich_sheet_payload_template_error_indicator():
    payload = {
        "modules": {"scheda_pg_markdown_template.md": "{{ invalid {{ syntax"},
        "export": {},
    }

    enriched = _enrich_sheet_payload(payload, ledger=None, source_url="http://source")

    assert enriched.get("sheet_render_error")
    assert "scheda_pg_markdown_template.md" in enriched["sheet_render_error"]
    assert not enriched.get("sheet_markdown")


async def _run_core_harvest(
    tmp_path,
    monkeypatch,
    *,
    skip_unchanged: bool = False,
    max_items: int | None = None,
    t1_filter: bool = False,
    t1_variants: int = 3,
):
    sample_payload = _make_sample_payload()
    sheet_payload = sample_payload["export"]["sheet_payload"]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/modules/minmax_builder.txt":
            return httpx.Response(200, json=sample_payload)
        if request.url.path == "/ruling":
            return httpx.Response(
                200, json={"ruling_badge": "validated", "sources": ["mock"]}
            )
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
        require_complete=True,
        skip_health_check=False,
        skip_unchanged=skip_unchanged,
        max_items=max_items,
        ruling_expert_url="http://mock.api/ruling",
        t1_filter=t1_filter,
        t1_variants=t1_variants,
    )

    return output_dir, index_path


def test_run_harvest_smoke(tmp_path, monkeypatch):
    output_dir, index_path = asyncio.run(_run_core_harvest(tmp_path, monkeypatch))

    saved_build = json.loads(
        (output_dir / "alchemist.json").read_text(encoding="utf-8")
    )
    assert (output_dir / "alchemist_lvl05.json").is_file()
    assert (output_dir / "alchemist_lvl10.json").is_file()
    assert saved_build["build_state"]["class"] == "Alchemist"
    rendered_sheet = saved_build["export"]["sheet_payload"].get("sheet_markdown")
    assert rendered_sheet
    assert "Alchemist Sample" in rendered_sheet
    assert "Velocità" in rendered_sheet
    assert "Tiri Salvezza:** Temp 5 / Riflessi 2 / Volontà 1" in rendered_sheet
    assert "**BAB:** 3 | **Iniziativa:** 4 | **Velocità:** 9" in rendered_sheet
    rendered_stats = saved_build["export"]["sheet_payload"].get("statistiche", {})
    for label, key in {
        "For": "FOR",
        "Des": "DES",
        "Cos": "COS",
        "Int": "INT",
        "Sag": "SAG",
        "Car": "CAR",
    }.items():
        value = rendered_stats[key]
        expected_mod = (int(value) - 10) // 2
        assert f"**{label}** {value} (mod {expected_mod})" in rendered_sheet

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert {entry["level"] for entry in index_payload["entries"]} == {1, 5, 10}
    assert any(
        entry["file"].endswith("alchemist_lvl05.json")
        for entry in index_payload["entries"]
    )
    assert any(
        entry["file"].endswith("alchemist_lvl10.json")
        for entry in index_payload["entries"]
    )


def test_run_harvest_honors_max_items(tmp_path, monkeypatch):
    output_dir, index_path = asyncio.run(
        _run_core_harvest(tmp_path, monkeypatch, max_items=2)
    )

    assert (output_dir / "alchemist.json").is_file()
    assert (output_dir / "alchemist_lvl05.json").is_file()
    assert not (output_dir / "alchemist_lvl10.json").exists()

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index_payload["entries"]) == 2
    assert {entry["level"] for entry in index_payload["entries"]} == {1, 5}


def test_run_harvest_t1_filter_selects_best_variant(tmp_path, monkeypatch):
    base_payload = _make_sample_payload()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/modules/minmax_builder.txt":
            call_no = handler.calls
            handler.calls += 1
            meta_tier = "T1" if call_no == 1 else "T2"
            offense = 10 + call_no * 2
            defense = 15 + call_no
            payload = copy.deepcopy(base_payload)
            payload["benchmark"]["meta_tier"] = meta_tier
            payload["benchmark"]["ruling_badge"] = "validated"
            payload["benchmark"]["statistics"].update(
                {"DPR_Base": offense, "ca": defense}
            )
            payload["ruling_log"] = [f"variante {call_no + 1}"]
            return httpx.Response(200, json=payload)
        if request.url.path == "/ruling":
            return httpx.Response(
                200, json={"ruling_badge": "validated", "sources": ["mock"]}
            )
        return httpx.Response(404)

    handler.calls = 0
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

    asyncio.run(
        run_harvest(
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
            require_complete=True,
            skip_health_check=False,
            skip_unchanged=False,
            max_items=None,
            ruling_expert_url="http://mock.api/ruling",
            t1_filter=True,
            t1_variants=3,
        )
    )

    saved_build = json.loads((output_dir / "alchemist.json").read_text(encoding="utf-8"))
    assert saved_build["benchmark"]["meta_tier"] == "T1"
    assert saved_build["benchmark"]["statistics"]["DPR_Base"] == 12
    assert saved_build["benchmark"]["statistics"]["ca"] == 16

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    entry = index_payload["entries"][0]
    assert entry["meta_tier"] == "T1"
    assert entry["benchmark_offense"] == 12
    assert entry["benchmark_defense"] == 16
    assert "variante 2" in entry["ruling_log"]


def test_run_harvest_t1_filter_errors_without_tier(tmp_path, monkeypatch):
    base_payload = _make_sample_payload()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/modules/minmax_builder.txt":
            payload = copy.deepcopy(base_payload)
            payload["benchmark"]["meta_tier"] = "T2"
            payload["benchmark"]["ruling_badge"] = "validated"
            payload["ruling_log"] = ["t1 mancante"]
            return httpx.Response(200, json=payload)
        if request.url.path == "/ruling":
            return httpx.Response(
                200, json={"ruling_badge": "validated", "sources": ["mock"]}
            )
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

    asyncio.run(
        run_harvest(
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
            require_complete=True,
            skip_health_check=False,
            skip_unchanged=False,
            max_items=None,
            ruling_expert_url="http://mock.api/ruling",
            t1_filter=True,
            t1_variants=2,
        )
    )

    assert not (output_dir / "alchemist.json").exists()
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    entry = index_payload["entries"][0]
    assert entry["status"] == "error"
    assert "Filtro T1" in entry["error"]


async def _run_incomplete_harvest(tmp_path, monkeypatch):
    incomplete_payload = {
        "build_state": {
            "class": "Fighter",
            "race": "Human",
            "archetype": "Base",
            "step_total": 8,
            "statistics": {},
        },
        "benchmark": {},
        "export": {"sheet_payload": {"nome": "Incomplete"}},
        "narrative": None,
        "ledger": {},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/modules/minmax_builder.txt":
            return httpx.Response(200, json=incomplete_payload)
        if request.url.path == "/ruling":
            return httpx.Response(
                200, json={"ruling_badge": "validated", "sources": ["mock"]}
            )
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
        [BuildRequest(class_name="Fighter", mode="core")],
        api_url="http://mock.api",
        api_key="mock-key",
        output_dir=output_dir,
        index_path=index_path,
        modules=[],
        modules_output_dir=modules_dir,
        module_index_path=module_index_path,
        concurrency=1,
        max_retries=0,
        spec_path=None,
        discover=False,
        include_filters=[],
        exclude_filters=[],
        strict=False,
        keep_invalid=True,
        require_complete=False,
        skip_health_check=False,
        ruling_expert_url="http://mock.api/ruling",
    )

    return output_dir, index_path


def test_run_harvest_skips_incomplete_payload(tmp_path, monkeypatch):
    output_dir, index_path = asyncio.run(_run_incomplete_harvest(tmp_path, monkeypatch))

    assert not (output_dir / "fighter.json").exists()
    assert not (output_dir / "fighter_lvl05.json").exists()
    assert not (output_dir / "fighter_lvl10.json").exists()
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index_payload["entries"]) == 3
    for entry in index_payload["entries"]:
        assert entry["status"] == "invalid"
        assert entry.get("completeness_errors")
        assert "Narrativa assente" in entry["error"]


def test_run_harvest_skips_unchanged_payload(tmp_path, monkeypatch):
    output_dir, _ = asyncio.run(_run_core_harvest(tmp_path, monkeypatch))

    target_file = output_dir / "alchemist.json"
    first_mtime = target_file.stat().st_mtime_ns
    original_content = target_file.read_text(encoding="utf-8")

    _, index_path = asyncio.run(
        _run_core_harvest(tmp_path, monkeypatch, skip_unchanged=True)
    )

    assert target_file.stat().st_mtime_ns == first_mtime
    assert target_file.read_text(encoding="utf-8") == original_content

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert all(entry["status"] == "ok" for entry in index_payload["entries"])


def test_enrich_sheet_payload_trims_markdown_whitespace():
    payload = {
        "export": {
            "sheet_payload": {"nome": "Trim Sample"},
            "modules": {
                "scheda_pg_markdown_template.md": "\n    Test: {{ nome }}   \n\n",
            },
        }
    }

    enriched = _enrich_sheet_payload(payload, ledger=None, source_url=None)

    assert enriched["sheet_markdown"] == "Test: Trim Sample"
    assert enriched["sheet_markdown"] == enriched["sheet_markdown"].strip()


def test_analyze_indices_archives_invalid_payloads(tmp_path):
    build_dir = tmp_path / "builds"
    module_dir = tmp_path / "modules"
    build_dir.mkdir()
    module_dir.mkdir()

    valid_build = build_dir / "valid.json"
    invalid_build = build_dir / "invalid.json"
    valid_build.write_text("{}", encoding="utf-8")
    invalid_build.write_text("{" "bad" ": true}", encoding="utf-8")

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
    report = analyze_indices(
        build_index_path, module_index_path, archive_dir=archive_dir
    )

    assert report["builds"]["invalid"] == 1
    assert report["builds"]["errors"] == 1
    assert report["modules"]["invalid"] == 1
    assert report["modules"]["errors"] == 1
    assert len(report["archived_files"]) == 2
    assert (archive_dir / "builds" / invalid_build.name).is_file()
    assert (archive_dir / "modules" / module_file.name).is_file()
