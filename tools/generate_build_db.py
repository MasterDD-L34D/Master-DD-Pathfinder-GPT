"""Utility per popolare il database locale di build MinMax Builder."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import textwrap
from fnmatch import fnmatchcase
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from itertools import islice, product
from pathlib import Path
from typing import Any, Iterable, List, Mapping, MutableMapping, Sequence

import yaml
from jinja2 import BaseLoader, ChainableUndefined
from jinja2.nativetypes import NativeEnvironment

import httpx
from jsonschema import Draft202012Validator, RefResolver
from jsonschema.exceptions import ValidationError

# Lista di classi PF1e target supportate dal builder
PF1E_CLASSES: List[str] = [
    "Alchemist",
    "Arcanist",
    "Barbarian",
    "Bard",
    "Bloodrager",
    "Brawler",
    "Cavalier",
    "Cleric",
    "Druid",
    "Fighter",
    "Gunslinger",
    "Hunter",
    "Inquisitor",
    "Investigator",
    "Kineticist",
    "Magus",
    "Medium",
    "Mesmerist",
    "Monk",
    "Ninja",
    "Occultist",
    "Oracle",
    "Paladin",
    "Psychic",
    "Ranger",
    "Rogue",
    "Samurai",
    "Shaman",
    "Skald",
    "Slayer",
    "Sorcerer",
    "Spiritualist",
    "Summoner",
    "Swashbuckler",
    "Warpriest",
    "Witch",
    "Wizard",
]

DEFAULT_MODE = "extended"
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_SPEC_FILE = (
    Path(__file__).resolve().parent.parent / "docs/examples/pg_variants.yml"
)
MODULE_ENDPOINT = "/modules/minmax_builder.txt"
MODULE_DUMP_ENDPOINT = "/modules/{name}"
MODULE_META_ENDPOINT = "/modules/{name}/meta"
MODULE_LIST_ENDPOINT = "/modules"

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
BUILD_SCHEMA_MAP = {
    "core": "build_core.schema.json",
    "extended": "build_extended.schema.json",
    "full-pg": "build_full_pg.schema.json",
}
MODULE_SCHEMA = "module_metadata.schema.json"

# Moduli "grezzi" utili per generare schede e flussi completi
DEFAULT_MODULE_TARGETS: Sequence[str] = (
    "base_profile.txt",
    "Taverna_NPC.txt",
    "narrative_flow.txt",
    "scheda_pg_markdown_template.md",
    "adventurer_ledger.txt",
)

# Moduli che vanno inclusi nel payload della scheda (solo il template da compilare)
SHEET_MODULE_TARGETS: Sequence[str] = ("scheda_pg_markdown_template.md",)


def now_iso_utc() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


@dataclass(slots=True)
class BuildRequest:
    class_name: str
    mode: str = DEFAULT_MODE
    level: int | None = None
    filename_prefix: str | None = None
    spec_id: str | None = None
    race: str | None = None
    archetype: str | None = None
    model: str | None = None
    background: str | None = None
    query_params: Mapping[str, object] = field(default_factory=dict)
    body_params: Mapping[str, object] = field(default_factory=dict)
    level_checkpoints: Sequence[int] = field(default_factory=lambda: (1, 5, 10))

    def http_method(self) -> str:
        return "POST" if self.body_params else "GET"

    def output_name(self) -> str:
        if self.filename_prefix:
            return self.filename_prefix
        if self.spec_id:
            return slugify(self.spec_id)
        return slugify(self.class_name)

    def metadata(self) -> Mapping[str, object | None]:
        resolved_race = (
            self.race
            or self.query_params.get("race")
            or self.body_params.get("race")
            or "Human"
        )

        resolved_archetype = (
            self.archetype
            or self.query_params.get("archetype")
            or self.query_params.get("model")
            or self.body_params.get("archetype")
            or self.body_params.get("model")
            or self.model
            or "Base"
        )

        resolved_background = (
            self.background
            or self.body_params.get("background")
            or self.body_params.get("background_hooks")
        )

        resolved_spec_id = self.spec_id or slugify(
            "_".join(
                str(part)
                for part in (
                    self.class_name,
                    resolved_race,
                    resolved_archetype,
                    resolved_background,
                )
                if part
            )
        )

        return {
            "class": self.class_name,
            "race": resolved_race,
            "archetype": resolved_archetype,
            "mode": self.mode,
            "mode_normalized": normalize_mode(self.mode),
            "spec_id": resolved_spec_id,
            "model": self.model,
            "background": resolved_background,
            "level": self.level,
            "level_checkpoints": list(self.level_checkpoints),
        }


class BuildFetchError(Exception):
    """Raised when the build API does not return usable data."""

    def __init__(
        self, message: str, *, completeness_errors: Sequence[str] | None = None
    ) -> None:
        super().__init__(message)
        self.completeness_errors = (
            list(completeness_errors) if completeness_errors is not None else None
        )


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def normalize_mode(mode: str) -> str:
    candidate = str(mode or DEFAULT_MODE).strip().lower()
    return "core" if candidate.startswith("core") else "extended"


def expected_step_total_for_mode(mode: str) -> int:
    normalized = normalize_mode(mode)
    return 8 if normalized == "core" else 16


def ensure_output_dirs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def _normalize_mapping(data: Mapping | None) -> Mapping[str, object]:
    return {str(key): value for key, value in (data or {}).items() if value is not None}


def _normalize_levels(
    levels: Sequence[int] | None, fallback: Sequence[int]
) -> list[int]:
    normalized: list[int] = []
    for level in levels or []:
        try:
            coerced = int(level)
        except (TypeError, ValueError):
            continue
        if coerced <= 0 or coerced in normalized:
            continue
        normalized.append(coerced)
    return normalized or list(fallback)


def _is_placeholder(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        lowered = value.strip().lower()
        return not lowered or "stub" in lowered or lowered in {"todo", "tbd"}
    if isinstance(value, Mapping):
        return all(_is_placeholder(v) for v in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return all(_is_placeholder(v) for v in value)
    return False


def _merge_prefer_existing(
    target: MutableMapping[str, object], *sources: Mapping
) -> MutableMapping[str, object]:
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key, value in source.items():
            if _is_placeholder(value):
                continue
            existing = target.get(key)
            if isinstance(existing, Mapping) and isinstance(value, Mapping):
                target[key] = _merge_prefer_existing(dict(existing), value)
            elif _is_placeholder(existing):
                target[key] = value
            elif key not in target:
                target[key] = value
    return target


def _first_non_placeholder(*values: object) -> object | None:
    for value in values:
        if not _is_placeholder(value):
            return value
    return None


def _merge_unique_list(
    existing: Sequence | None, *sources: Sequence | None
) -> list[object]:
    merged: list[object] = []
    if isinstance(existing, Sequence) and not isinstance(existing, (str, bytes)):
        merged.extend(existing)
    for source in sources:
        if not isinstance(source, Sequence) or isinstance(source, (str, bytes)):
            continue
        for item in source:
            if item not in merged:
                merged.append(item)
    return merged


def _has_content(value: object) -> bool:
    if value is None:
        return False
    if _is_placeholder(value):
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_content(v) for v in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_has_content(v) for v in value)
    return True


def _load_local_modules(module_names: Sequence[str]) -> Mapping[str, str]:
    candidates = [
        Path("src/data/modules"),
        Path("src/modules"),
        Path("modules"),
    ]
    loaded: dict[str, str] = {}
    for name in module_names:
        if name in loaded:
            continue
        for base_path in candidates:
            path = base_path / name
            if path.is_file():
                loaded[name] = path.read_text(encoding="utf-8")
                break
    return loaded


def _style_hint(label: object) -> str | None:
    return None if label is None else str(label)


def _get_total_level(classes: Sequence | None) -> int | None:
    total = 0
    for cls in classes or []:
        if isinstance(cls, Mapping):
            level = cls.get("livelli") or cls.get("levels") or cls.get("level")
        else:
            level = cls
        if level is None:
            continue
        try:
            total += int(level)
        except (TypeError, ValueError):
            continue
    return total if total > 0 else None


def _lookup_meta_badges(*_: object, **__: object) -> str | None:
    return None


def _rules_status_text(*_: object, **__: object) -> str | None:
    return None


def _source_mix_summary(*_: object, **__: object) -> str | None:
    return None


def _coerce_number(value: object, default: object | None = None) -> object:
    if isinstance(value, (int, float)):
        return value
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        try:
            return float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default


def _truncate_sequence_by_level(
    entries: Sequence | None, target_level: int | None
) -> list[object] | None:
    if target_level is None:
        return None
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        return None

    kept: list[object] = []
    current_level = 0

    for entry in entries:
        if isinstance(entry, Mapping):
            absolute_level = _coerce_number(entry.get("livello"))
            if isinstance(absolute_level, (int, float)):
                try:
                    coerced = int(absolute_level)
                except (TypeError, ValueError):
                    coerced = None
                if coerced is not None:
                    if coerced > target_level:
                        break
                    kept.append(entry)
                    current_level = max(current_level, coerced)
                    continue

        level_increment: int | None = None
        if isinstance(entry, Mapping):
            for classes_key in ("classi", "classes"):
                if classes_key in entry:
                    level_increment = _get_total_level(entry.get(classes_key))
                    break
            if level_increment is None:
                level_increment = _coerce_number(
                    entry.get("livello") or entry.get("level")
                )

        try:
            increment = int(level_increment) if level_increment is not None else 1
        except (TypeError, ValueError):
            increment = 1

        if increment <= 0:
            increment = 1

        if current_level + increment > target_level:
            break

        kept.append(entry)
        current_level += increment

        if current_level >= target_level:
            break

    return kept


_sheet_template_env = NativeEnvironment(
    loader=BaseLoader(),
    autoescape=False,
    undefined=ChainableUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)
_sheet_template_env.globals.update(
    style_hint=_style_hint,
    get_total_level=_get_total_level,
    lookup_meta_badges=_lookup_meta_badges,
    rules_status_text=_rules_status_text,
    source_mix_summary=_source_mix_summary,
)


def _render_sheet_template(template_text: str, context: Mapping[str, object]) -> str:
    template = _sheet_template_env.from_string(template_text)
    render_ctx: dict[str, object] = dict(context)
    numeric_keys = {
        "AC_arm",
        "AC_scudo",
        "AC_des",
        "AC_defl",
        "AC_nat",
        "AC_dodge",
        "AC_misc",
        "AC_base",
        "AC_tot",
        "CA_touch",
        "CA_ff",
        "BAB",
        "pf_totali",
        "pf_per_livello",
        "speed",
        "velocita",
        "init",
        "iniziativa",
        "CMB",
        "CMD",
        "CMD_base",
        "size_mod_cmd",
        "cmd_altro",
        "gp_totali",
        "gp_investiti",
        "gp_liquidi",
        "gp",
        "pp",
        "sp",
        "cp",
        "wbl_target_gp",
        "wbl_delta_gp",
        "next_wbl_gp",
    }
    for key in numeric_keys:
        render_ctx[key] = _coerce_number(render_ctx.get(key), 0)

    stats = render_ctx.get("statistiche")
    if isinstance(stats, Mapping):
        render_ctx["statistiche"] = {
            stat_key: _coerce_number(stat_val, stat_val)
            for stat_key, stat_val in stats.items()
        }

    stats_key = render_ctx.get("statistiche_chiave")
    if isinstance(stats_key, Mapping):
        render_ctx["statistiche_chiave"] = {
            stat_key: _coerce_number(stat_val, stat_val)
            for stat_key, stat_val in stats_key.items()
        }

    rendered = template.render(**render_ctx)
    return rendered.strip()


_validator_cache: dict[str, Draft202012Validator] = {}
_schema_store: dict[str, Mapping] = {}


def _bootstrap_schema_store() -> None:
    """Preload every local schema so $id references resolve offline."""

    if _schema_store.get("__bootstrapped__"):
        return

    for path in SCHEMAS_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        _schema_store[path.name] = schema
        if "$id" in schema:
            _schema_store[schema["$id"]] = schema

    _schema_store["__bootstrapped__"] = {"loaded": True}


def _load_validator(schema_filename: str) -> Draft202012Validator:
    _bootstrap_schema_store()
    path = SCHEMAS_DIR / schema_filename
    if not path.is_file():
        raise FileNotFoundError(f"Schema non trovato: {path}")

    schema = json.loads(path.read_text(encoding="utf-8"))
    _schema_store[schema_filename] = schema
    if "$id" in schema:
        _schema_store[schema["$id"]] = schema
    resolver = RefResolver(
        base_uri=path.resolve().as_uri(), referrer=schema, store=_schema_store
    )
    return Draft202012Validator(schema, resolver=resolver)


def get_validator(schema_filename: str) -> Draft202012Validator:
    if schema_filename not in _validator_cache:
        _validator_cache[schema_filename] = _load_validator(schema_filename)
    return _validator_cache[schema_filename]


def schema_for_mode(mode: str) -> str:
    normalized = mode.lower()
    return BUILD_SCHEMA_MAP.get(normalized, BUILD_SCHEMA_MAP[DEFAULT_MODE])


def validate_with_schema(
    schema_filename: str, payload: Mapping, context: str, *, strict: bool
) -> str | None:
    validator = get_validator(schema_filename)
    errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
    if not errors:
        return None

    message = "; ".join(error.message for error in errors)
    log_fn = logging.error if strict else logging.warning
    log_fn(
        "Payload %s non valido (%s): %s",
        context,
        schema_filename,
        message,
        extra={
            "event": "schema_validation_failed",
            "context": context,
            "schema": schema_filename,
            "errors": [error.message for error in errors],
            "paths": [
                "/".join(str(segment) for segment in error.path) for error in errors
            ],
        },
    )
    if strict:
        raise ValidationError(message)
    return message


def _empty_review_section() -> dict[str, Any]:
    return {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "errors": 0,
        "missing": 0,
        "entries": [],
    }


def _bump_review(section: MutableMapping[str, Any], status: str) -> None:
    section["total"] += 1
    if status == "ok":
        section["valid"] += 1
    elif status == "invalid":
        section["invalid"] += 1
    elif status == "missing":
        section["missing"] += 1
    else:
        section["errors"] += 1


def _bump_checkpoint(
    checkpoints: MutableMapping[str, MutableMapping[str, int]],
    level: int | str | None,
    status: str,
    *,
    schema_error: bool = False,
    completeness_error: bool = False,
) -> None:
    if level is None:
        return

    try:
        level_key = f"{int(level)}"
    except (TypeError, ValueError):
        return

    bucket = checkpoints.setdefault(
        level_key,
        {
            "total": 0,
            "invalid": 0,
            "schema_errors": 0,
            "completeness_errors": 0,
        },
    )
    bucket["total"] += 1
    if status != "ok":
        bucket["invalid"] += 1
    if schema_error:
        bucket["schema_errors"] += 1
    if completeness_error:
        bucket["completeness_errors"] += 1


def _checkpoint_summary_from_entries(
    entries: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, int]]:
    checkpoints: dict[str, dict[str, int]] = {}
    for entry in entries:
        _bump_checkpoint(
            checkpoints,
            entry.get("level"),
            str(entry.get("status") or "ok"),
            schema_error=bool(entry.get("error")),
            completeness_error=bool(entry.get("completeness_errors")),
        )

    return {
        key: checkpoints[key] for key in sorted(checkpoints, key=lambda item: int(item))
    }


def _load_build_index_entries(
    build_index_path: Path | None,
) -> dict[Path, Mapping[str, object]]:
    if not build_index_path or not build_index_path.is_file():
        return {}

    try:
        build_index_payload = json.loads(build_index_path.read_text(encoding="utf-8"))
        raw_entries: Sequence[Mapping[str, object]] = (
            build_index_payload.get("entries") or []
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logging.warning(
            "Impossibile leggere l'indice build %s: %s", build_index_path, exc
        )
        return {}

    entries: dict[Path, Mapping[str, object]] = {}
    for entry in raw_entries:
        file_path = entry.get("file")
        if not file_path:
            continue
        resolved = Path(str(file_path)).resolve()
        entries[resolved] = entry
    return entries


def _worst_status(*statuses: str | None) -> str:
    priority = {"error": 4, "missing": 3, "invalid": 2, "ok": 1, None: 0}
    return max(statuses, key=lambda status: priority.get(status, 0)) or "ok"


def _requested_level(payload: Mapping[str, object] | None) -> int | None:
    if not isinstance(payload, Mapping):
        return None

    request_ctx = (
        payload.get("request") if isinstance(payload.get("request"), Mapping) else {}
    )
    level = request_ctx.get("level") if isinstance(request_ctx, Mapping) else None
    if level is None and isinstance(payload.get("build_state"), Mapping):
        level = payload.get("build_state", {}).get("level")

    try:
        coerced = int(level)
    except (TypeError, ValueError):
        return None

    return coerced if coerced > 0 else None


def review_local_database(
    build_dir: Path,
    module_dir: Path,
    *,
    build_index_path: Path | None = None,
    module_index_path: Path | None = None,
    strict: bool = False,
    output_path: Path | None = None,
) -> Mapping[str, Any]:
    """Valida i JSON già presenti nel database locale e produce un report riassuntivo."""

    builds_section = _empty_review_section()
    modules_section = _empty_review_section()
    checkpoints: dict[str, dict[str, int]] = {}

    build_index_meta: dict[str, object] = {}
    if build_index_path and build_index_path.is_file():
        try:
            existing_index = json.loads(build_index_path.read_text(encoding="utf-8"))
            build_index_meta.update(
                {
                    "api_url": existing_index.get("api_url"),
                    "mode": existing_index.get("mode"),
                    "spec_file": existing_index.get("spec_file"),
                }
            )
        except Exception:
            pass

    build_index_entries = _load_build_index_entries(build_index_path)
    build_files: dict[Path, str] = {}
    index_entries: list[dict[str, object]] = []
    if build_dir.is_dir():
        for path in build_dir.rglob("*.json"):
            if path.is_file():
                build_files[path.resolve()] = str(path)
    for resolved_path in build_index_entries:
        build_files.setdefault(
            resolved_path,
            str(build_index_entries[resolved_path].get("file") or resolved_path),
        )

    for path, display_path in sorted(build_files.items(), key=lambda item: item[1]):
        entry: dict[str, Any] = {"file": display_path}
        payload: Mapping[str, Any] | None = None
        index_entry = build_index_entries.get(path)
        target_level = index_entry.get("level") if index_entry else None
        validation_error: str | None = None
        completeness_errors: list[str] = []
        if index_entry:
            entry.update(
                {k: v for k, v in index_entry.items() if k not in {"file", "status"}}
            )

        if not path.exists():
            status = _worst_status(
                "missing", str(index_entry.get("status")) if index_entry else None
            )
            entry["status"] = status
            entry["error"] = "File mancante"
            _bump_review(builds_section, status)
            _bump_checkpoint(checkpoints, target_level, status)
            builds_section["entries"].append(entry)
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            entry.update(
                {
                    "class": payload.get("class")
                    or (payload.get("build_state") or {}).get("class"),
                    "mode": payload.get("mode"),
                }
            )
            validation_error = validate_with_schema(
                schema_for_mode(payload.get("mode", DEFAULT_MODE)),
                payload,
                f"build {path.name}",
                strict=strict,
            )
            sheet_payload = payload.get("export", {}).get(
                "sheet_payload"
            ) or payload.get("sheet_payload")
            sheet_error = None
            if sheet_payload is not None:
                sheet_error = validate_with_schema(
                    "scheda_pg.schema.json",
                    sheet_payload,
                    f"sheet payload {path.name}",
                    strict=strict,
                )
            if validation_error and sheet_error:
                validation_error = f"{validation_error}; {sheet_error}"
            elif validation_error is None:
                validation_error = sheet_error

            completeness_ctx = (
                payload.get("completeness")
                if isinstance(payload.get("completeness"), Mapping)
                else {}
            )
            completeness_errors = list(completeness_ctx.get("errors") or [])
            target_level = _requested_level(payload) or target_level
            progression_errors = _progression_level_errors(sheet_payload, target_level)
            for error in progression_errors:
                if error not in completeness_errors:
                    completeness_errors.append(error)
            completeness_text: str | None = None
            if completeness_errors:
                completeness_text = "; ".join(
                    str(error) for error in completeness_errors
                )
                validation_error = (
                    completeness_text
                    if validation_error is None
                    else f"{validation_error}; {completeness_text}"
                )

            validation_status = "ok" if validation_error is None else "invalid"
            completeness_status = "invalid" if completeness_errors else "ok"
            status = _worst_status(validation_status, completeness_status)
            if completeness_errors:
                entry["completeness_errors"] = completeness_errors
            if validation_error:
                entry["error"] = validation_error
        except ValidationError:
            raise
        except Exception as exc:
            status = "error"
            entry["error"] = str(exc)

        status = _worst_status(
            status, str(index_entry.get("status")) if index_entry else None
        )
        if "error" not in entry and index_entry and index_entry.get("error"):
            entry["error"] = index_entry["error"]
        entry["status"] = status
        if target_level:
            entry["level"] = target_level
        _bump_review(builds_section, status)
        _bump_checkpoint(
            checkpoints,
            target_level,
            status,
            schema_error=bool(validation_error),
            completeness_error=bool(completeness_errors),
        )
        builds_section["entries"].append(entry)

        class_name = (
            entry.get("class")
            or (payload or {}).get("class")
            or ((payload or {}).get("build_state") or {}).get("class")
        )
        race = (payload or {}).get("race") or (
            (payload or {}).get("build_state") or {}
        ).get("race")
        archetype = (
            (payload or {}).get("archetype")
            or ((payload or {}).get("build_state") or {}).get("archetype")
            or ((payload or {}).get("build_state") or {}).get("model")
        )
        background = (payload or {}).get("background")
        mode = (payload or {}).get("mode") or (
            (payload or {}).get("build_state") or {}
        ).get("mode")
        spec_parts = [class_name, race, archetype, background]
        spec_id = (
            slugify("_".join(str(part) for part in spec_parts if part))
            if any(spec_parts)
            else None
        )

        preserved_metadata = {
            k: v
            for k, v in (index_entry or {}).items()
            if k
            not in {
                "file",
                "status",
                "error",
                "completeness_errors",
            }
        }
        level_checkpoints = _normalize_levels(
            preserved_metadata.get("level_checkpoints")
            or preserved_metadata.get("levels"),
            (1, 5, 10),
        )
        output_prefix = preserved_metadata.get("output_prefix") or spec_id
        if not output_prefix and display_path:
            output_prefix = Path(display_path).stem

        index_entry = {
            "file": display_path,
            "status": status,
            "output_prefix": output_prefix,
            "class": class_name,
            "race": race,
            "archetype": archetype,
            "mode": mode,
            "mode_normalized": normalize_mode(mode or DEFAULT_MODE),
            "spec_id": spec_id,
            "background": background or preserved_metadata.get("background"),
            "model": preserved_metadata.get("model"),
            "level_checkpoints": level_checkpoints,
        }
        if target_level:
            index_entry["level"] = target_level
        for field in (
            "step_total",
            "expected_step_total",
            "extended_steps_available",
            "step_total_ok",
        ):
            if preserved_metadata.get(field) is not None:
                index_entry[field] = preserved_metadata[field]
        if validation_error:
            index_entry["error"] = validation_error
        if completeness_errors:
            index_entry["completeness_errors"] = completeness_errors
        entry.setdefault("output_prefix", index_entry.get("output_prefix"))
        entry.setdefault("level_checkpoints", index_entry.get("level_checkpoints"))
        entry.setdefault("spec_id", index_entry.get("spec_id"))
        entry.setdefault("mode_normalized", index_entry.get("mode_normalized"))
        index_entries.append(index_entry)

    module_entries: Sequence[Mapping[str, Any]] = []
    if module_index_path and module_index_path.is_file():
        try:
            module_index_payload = json.loads(
                module_index_path.read_text(encoding="utf-8")
            )
            module_entries = module_index_payload.get("entries", []) or []
        except Exception as exc:
            modules_section["entries"].append(
                {"file": str(module_index_path), "status": "error", "error": str(exc)}
            )
            _bump_review(modules_section, "error")
            module_entries = []
    elif module_dir.is_dir():
        module_entries = [
            {
                "module": path.name,
                "file": str(path),
                "meta": {
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                    "suffix": path.suffix,
                },
            }
            for path in sorted(module_dir.iterdir())
            if path.is_file()
        ]

    for module_entry in module_entries:
        module_name = str(module_entry.get("module") or "")
        resolved_path = Path(module_entry.get("file") or module_dir / module_name)
        entry: dict[str, Any] = {
            "module": module_name or resolved_path.name,
            "file": str(resolved_path),
        }

        if not resolved_path.exists():
            entry["status"] = "missing"
            entry["error"] = "File mancante"
            _bump_review(modules_section, "missing")
            modules_section["entries"].append(entry)
            continue

        try:
            validation_error = validate_with_schema(
                MODULE_SCHEMA,
                module_entry.get("meta", {}),
                f"module meta {entry['module']}",
                strict=strict,
            )
            status = "ok" if validation_error is None else "invalid"
            if validation_error:
                entry["error"] = validation_error
        except ValidationError:
            raise
        except Exception as exc:
            status = "error"
            entry["error"] = str(exc)

        entry["status"] = status
        entry["size_bytes"] = (
            module_entry.get("meta", {}).get("size_bytes")
            or resolved_path.stat().st_size
        )
        _bump_review(modules_section, status)
        modules_section["entries"].append(entry)

    if checkpoints:
        builds_section["checkpoints"] = {
            key: checkpoints[key]
            for key in sorted(checkpoints, key=lambda item: int(item))
        }

    report = {
        "generated_at": now_iso_utc(),
        "builds": builds_section,
        "modules": modules_section,
    }

    if build_index_path:
        report["build_index"] = str(build_index_path)
    if module_index_path:
        report["module_index"] = str(module_index_path)

    if build_index_path:
        index_payload: dict[str, object] = {
            "generated_at": now_iso_utc(),
            **build_index_meta,
            "entries": sorted(
                index_entries, key=lambda entry: str(entry.get("file") or "")
            ),
        }
        index_payload["checkpoints"] = _checkpoint_summary_from_entries(index_entries)
        write_json(build_index_path, index_payload)

    if output_path:
        write_json(output_path, report)
        logging.info("Report di review scritto in %s", output_path)

    return report


def apply_glob_filters(
    entries: Sequence[str], include: Sequence[str], exclude: Sequence[str]
) -> list[str]:
    def matches(patterns: Sequence[str], candidate: str) -> bool:
        return any(fnmatchcase(candidate, pattern) for pattern in patterns)

    filtered: list[str] = []
    for name in entries:
        if include and not matches(include, name):
            continue
        if exclude and matches(exclude, name):
            continue
        filtered.append(name)
    return filtered


def load_spec_requests(spec_path: Path, default_mode: str) -> list[BuildRequest]:
    """Carica un file YAML/JSON e restituisce le richieste strutturate."""

    raw_data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if raw_data is None:
        raise ValueError(f"File spec vuoto: {spec_path}")

    if isinstance(raw_data, Mapping):
        default_mode = str(raw_data.get("mode", default_mode))
        default_levels = _normalize_levels(
            raw_data.get("level_checkpoints"), (1, 5, 10)
        )
        entries = raw_data.get("requests")
    else:
        default_levels = _normalize_levels(None, (1, 5, 10))
        entries = raw_data

    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        raise ValueError(f"Spec {spec_path} non valida: atteso elenco di richieste")

    requests: list[BuildRequest] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError(f"Voce spec non valida: {entry!r}")

        class_name = entry.get("class")
        if not class_name:
            raise ValueError(f"Voce spec senza 'class': {entry}")

        request = BuildRequest(
            class_name=str(class_name),
            mode=str(entry.get("mode", default_mode)),
            filename_prefix=entry.get("output_prefix") or entry.get("filename_prefix"),
            spec_id=entry.get("id") or entry.get("name"),
            race=entry.get("race"),
            archetype=entry.get("archetype") or entry.get("model"),
            model=entry.get("model"),
            background=entry.get("background") or entry.get("background_hooks"),
            query_params=_normalize_mapping(
                entry.get("query") or entry.get("query_params") or entry.get("params")
            ),
            body_params=_normalize_mapping(
                entry.get("body") or entry.get("body_params") or entry.get("json")
            ),
            level_checkpoints=_normalize_levels(
                entry.get("level_checkpoints") or entry.get("levels"), default_levels
            ),
        )

        requests.append(request)

    return requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera un database JSON di build per classe."
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("API_URL", DEFAULT_BASE_URL),
        help="Base URL dell'API Master DD (default: %(default)s)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("API_KEY"),
        help="API key da passare nell'header x-api-key (default: variabile API_KEY)",
    )
    parser.add_argument(
        "--ruling-expert-url",
        dest="ruling_expert_url",
        default=os.environ.get("RULING_EXPERT_URL"),
        help="Endpoint REST del Ruling Expert per convalidare il badge (obbligatorio)",
    )
    parser.add_argument(
        "--ruling-expert-timeout",
        dest="ruling_timeout",
        type=float,
        default=30.0,
        help="Timeout (secondi) per la chiamata verso Ruling Expert (default: %(default)s)",
    )
    parser.add_argument(
        "--ruling-expert-max-retries",
        dest="ruling_max_retries",
        type=int,
        help="Retry massimo per la chiamata Ruling Expert (default: usa --max-retries)",
    )
    parser.add_argument(
        "--mode",
        default=DEFAULT_MODE,
        choices=["core", "extended", "full-pg"],
        help="Modalità di flow da richiedere al builder (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("src/data/builds"),
        help="Directory di output per i singoli JSON",
    )
    parser.add_argument(
        "--modules-output-dir",
        type=Path,
        default=Path("src/data/modules"),
        help="Directory di output per i dump grezzi dei moduli",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=Path("src/data/build_index.json"),
        help="Percorso del file indice riassuntivo",
    )
    parser.add_argument(
        "--module-index-path",
        type=Path,
        default=Path("src/data/module_index.json"),
        help="Percorso del file indice per i moduli scaricati",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Numero massimo di richieste concorrenti (default: %(default)s)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Numero massimo di tentativi per ogni richiesta (default: %(default)s)",
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        default=list(DEFAULT_MODULE_TARGETS),
        help="Elenco moduli da scaricare in parallelo alle build",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Interrompe l'esecuzione al primo errore di validazione",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Continua l'esecuzione loggando gli errori di validazione (default)",
    )
    parser.add_argument(
        "--keep-invalid",
        action="store_true",
        help="Scrive comunque i payload non validi invece di scartarli",
    )
    parser.add_argument(
        "--require-complete",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Considera incompleti i payload privi di statistiche/narrativa/ledger e riprova automaticamente",
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Salta il controllo di raggiungibilità dell'API (fallback per ambienti in cui /health non è disponibile)",
    )
    parser.add_argument(
        "--skip-unchanged",
        action="store_true",
        help="Evita di riscrivere i payload invariati confrontando i JSON generati con i file già presenti",
    )
    parser.add_argument(
        "--dual-pass",
        action="store_true",
        help="Esegue prima un passaggio fail-fast (--strict) e poi uno tollerante con --keep-invalid",
    )
    parser.add_argument(
        "--dual-pass-report",
        type=Path,
        help="Percorso del report riepilogativo dei due passaggi (--dual-pass)",
    )
    parser.add_argument(
        "--invalid-archive-dir",
        type=Path,
        help="Cartella in cui copiare i payload non conformi individuati negli indici",
    )
    parser.add_argument(
        "--validate-db",
        action="store_true",
        help="Valida il database locale (build e moduli) senza effettuare chiamate all'API, producendo un report per livello",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=Path("src/data/build_review.json"),
        help="Percorso del report di review (con riepilogo per checkpoint di livello) quando --validate-db è attivo (default: %(default)s)",
    )
    parser.add_argument(
        "--discover-modules",
        action="store_true",
        help="Recupera automaticamente la lista di moduli disponibili da /modules",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=[],
        metavar="GLOB",
        help="Filtri di inclusione (glob) applicati ai moduli scoperti via /modules",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        metavar="GLOB",
        help="Filtri di esclusione (glob) applicati ai moduli scoperti via /modules",
    )
    parser.add_argument(
        "--spec-file",
        type=Path,
        help="File YAML/JSON con le richieste da processare (override di --mode/--classes)",
    )
    parser.add_argument(
        "--races",
        nargs="*",
        default=[],
        help="Elenco di razze da combinare con le classi target (prodotto cartesiano)",
    )
    parser.add_argument(
        "--archetypes",
        nargs="*",
        default=[],
        help="Elenco di archetipi/modelli da combinare con le classi target",
    )
    parser.add_argument(
        "--background-hooks",
        nargs="*",
        default=[],
        help="Hook di background da includere nel prodotto cartesiano",
    )
    parser.add_argument(
        "--classes",
        dest="filter_classes",
        nargs="*",
        help=(
            "Filtra le richieste generate a un sottoinsieme di classi PF1e (case-insensitive); "
            "applicato dopo spec/CLI"
        ),
    )
    parser.add_argument(
        "--levels",
        dest="filter_levels",
        nargs="*",
        type=int,
        help=(
            "Filtra i checkpoint di livello per ogni richiesta (es. --levels 1 5). "
            "Se una richiesta prevede un livello singolo non presente qui viene scartata"
        ),
    )
    parser.add_argument(
        "--max-items",
        type=int,
        help=(
            "Numero massimo di file di build da generare in una singola esecuzione "
            "dopo l'applicazione dei filtri di classe/livello"
        ),
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help=(
            "Numero di richieste già processate da saltare prima di applicare max-items "
            "(partendo da 0)"
        ),
    )
    parser.add_argument(
        "--page",
        type=int,
        help=(
            "Numero di pagina (1-based) da processare: calcola l'offset automaticamente "
            "se combinato con --page-size o --max-items"
        ),
    )
    parser.add_argument(
        "--page-size",
        type=int,
        help=(
            "Dimensione della pagina da usare con --page; se omessa, usa --max-items come"
            " valore di riferimento"
        ),
    )
    parser.add_argument(
        "classes",
        nargs="*",
        default=PF1E_CLASSES,
        help="Sovrascrive la lista di classi PF1e da generare",
    )
    return parser.parse_args()


def build_variant_matrix_requests(
    classes: Sequence[str],
    mode: str,
    races: Sequence[str],
    archetypes: Sequence[str],
    background_hooks: Sequence[str],
) -> list[BuildRequest]:
    race_options = list(races) or [None]
    archetype_options = list(archetypes) or [None]
    background_options = list(background_hooks) or [None]

    requests: list[BuildRequest] = []
    for class_name, race, archetype, background in product(
        classes, race_options, archetype_options, background_options
    ):
        spec_fragments = [class_name, race or "Human", archetype or "Base"]
        background_slug = slugify(background) if background else None
        if background_slug:
            spec_fragments.append(background_slug)

        spec_id = "::".join(spec_fragments)
        output_prefix = slugify("-".join(spec_fragments))
        query_params = _normalize_mapping({"race": race, "archetype": archetype})
        body_params = _normalize_mapping({"background_hooks": background})

        requests.append(
            BuildRequest(
                class_name=class_name,
                mode=mode,
                filename_prefix=output_prefix,
                spec_id=spec_id,
                race=race,
                archetype=archetype,
                background=background,
                query_params=query_params,
                body_params=body_params,
            )
        )

    return requests


def build_requests_from_args(args: argparse.Namespace) -> list[BuildRequest]:
    if args.spec_file:
        return load_spec_requests(args.spec_file, args.mode)

    if args.races or args.archetypes or args.background_hooks:
        return build_variant_matrix_requests(
            args.classes,
            args.mode,
            args.races,
            args.archetypes,
            args.background_hooks,
        )

    if DEFAULT_SPEC_FILE.is_file():
        logging.info("Uso il file spec predefinito %s", DEFAULT_SPEC_FILE)
        return load_spec_requests(DEFAULT_SPEC_FILE, args.mode)

    return [
        BuildRequest(class_name=class_name, mode=args.mode)
        for class_name in args.classes
    ]


def filter_requests(
    requests: Sequence[BuildRequest],
    class_filters: Sequence[str] | None,
    level_filters: Sequence[int] | None,
) -> list[BuildRequest]:
    class_set = (
        {slugify(name).lower() for name in class_filters if name}
        if class_filters
        else None
    )
    level_set = {int(level) for level in level_filters} if level_filters else None

    filtered_requests: list[BuildRequest] = []
    for request in requests:
        if class_set and slugify(request.class_name).lower() not in class_set:
            continue

        updated_request = request
        if level_set is not None:
            request_level = None
            try:
                request_level = (
                    int(request.level) if request.level is not None else None
                )
            except (TypeError, ValueError):
                request_level = None

            if request_level is not None and request_level not in level_set:
                continue

            filtered_levels = [
                coerced
                for coerced in (
                    int(lvl) for lvl in request.level_checkpoints if lvl is not None
                )
                if coerced in level_set
            ]
            updated_request = replace(request, level_checkpoints=filtered_levels)

        filtered_requests.append(updated_request)

    return filtered_requests


def _request_identifier(request: BuildRequest) -> str:
    return (
        request.spec_id
        or request.filename_prefix
        or request.output_name()
        or request.class_name
    )


def log_request_batch(
    requests: Sequence[BuildRequest],
    window: Mapping[str, int | None],
) -> None:
    offset = window.get("offset")
    limit = window.get("limit")
    start = window.get("start")
    end = window.get("end")
    total = window.get("total")

    if not requests:
        logging.info(
            "Nessuna richiesta selezionata (offset=%s, max_items=%s su totale %s)",
            offset,
            limit if limit is not None else "all",
            total,
        )
        return

    first = _request_identifier(requests[0])
    last = _request_identifier(requests[-1])

    logging.info(
        "Batch selezionato: offset=%s, max_items=%s, richieste %s-%s/%s (%s -> %s)",
        offset,
        limit if limit is not None else "all",
        start,
        (end - 1) if end is not None else start,
        total,
        first,
        last,
    )


def select_request_window(
    requests: Sequence[BuildRequest],
    *,
    offset: int = 0,
    max_items: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[list[BuildRequest], dict[str, int | None]]:
    total = len(requests)

    normalized_max_items = int(max_items) if max_items is not None else None
    effective_offset = max(0, int(offset or 0))

    if normalized_max_items is not None:
        normalized_max_items = max(0, normalized_max_items)
        if normalized_max_items == 0:
            return [], {
                "offset": effective_offset,
                "start": min(effective_offset, total),
                "end": min(effective_offset, total),
                "limit": 0,
                "total": total,
            }

    if page is not None:
        page_num = max(1, int(page))
        effective_page_size = page_size or normalized_max_items
        if effective_page_size is None or effective_page_size <= 0:
            raise ValueError(
                "--page richiede un --page-size valido o un --max-items positivo per calcolare la finestra"
            )
        effective_offset = (page_num - 1) * effective_page_size
        if normalized_max_items is None:
            normalized_max_items = effective_page_size

    start_index = min(effective_offset, total)
    end_index = (
        total
        if normalized_max_items is None
        else min(start_index + normalized_max_items, total)
    )

    selected = list(islice(requests, start_index, end_index))

    return selected, {
        "offset": effective_offset,
        "start": start_index,
        "end": end_index,
        "limit": normalized_max_items,
        "total": total,
    }


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, object] | None = None,
    json_body: Mapping[str, object] | None = None,
    timeout: int | float | None = None,
    max_retries: int,
    backoff_factor: float = 1.0,
) -> httpx.Response:
    attempt = 0
    while True:
        try:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout,
            )
        except httpx.RequestError as exc:
            if attempt >= max_retries:
                raise

            delay = backoff_factor * 2**attempt
            attempt += 1
            logging.warning(
                "Tentativo fallito per %s %s (%s). Retry in %.1fs...",
                method,
                url,
                exc.__class__.__name__,
                delay,
            )
            await asyncio.sleep(delay)
            continue

        if response.status_code not in {429} and response.status_code < 500:
            response.raise_for_status()
            return response

        if attempt >= max_retries:
            response.raise_for_status()

        delay = backoff_factor * 2**attempt
        attempt += 1
        logging.warning(
            "Tentativo fallito per %s %s (status %s). Retry in %.1fs...",
            method,
            url,
            response.status_code,
            delay,
        )
        await asyncio.sleep(delay)


async def assert_api_reachable(
    client: httpx.AsyncClient, api_key: str | None, health_path: str = "/health"
) -> None:
    """Fail fast with a clear message if the API endpoint is unreachable."""

    headers = {"x-api-key": api_key} if api_key else {}
    try:
        response = await client.get(health_path, headers=headers, timeout=5)
    except httpx.RequestError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(
            f"API non raggiungibile su {client.base_url}: {exc}. "
            "Avvia il servizio localmente oppure passa --api-url verso un endpoint accessibile."
        ) from exc

    if response.status_code == 404:
        logging.info(
            "L'endpoint %s non esiste su %s ma l'host risponde: proseguo...",
            health_path,
            client.base_url,
        )
    elif response.status_code >= 500:
        logging.warning(
            "Health check %s ha risposto %s: il servizio potrebbe non essere pronto",
            client.base_url,
            response.status_code,
        )


def _enrich_sheet_payload(
    payload: Mapping[str, object],
    ledger: Mapping | None,
    source_url: str | None,
) -> MutableMapping[str, object]:
    export_ctx = payload.get("export") if isinstance(payload, Mapping) else {}
    export_ctx = export_ctx or {}

    def _as_mapping(value: object) -> Mapping | None:
        return value if isinstance(value, Mapping) else None

    def _fallback_stat(label: str) -> str:
        return f"n/d ({label} non fornito)"

    def _normalize_save_entry(
        raw: object,
        breakdown: Mapping | None,
        fallback_total: int | float | None = None,
        label: str | None = None,
    ) -> Mapping[str, object]:
        entry: dict[str, object] = {}
        as_mapping = _as_mapping(raw) or {}
        total = _first_non_placeholder(
            as_mapping.get("totale"),
            as_mapping.get("total"),
            as_mapping.get("value"),
            raw if isinstance(raw, (int, float)) else None,
        )
        entry["base"] = _first_non_placeholder(
            as_mapping.get("base"), as_mapping.get("bab"), None
        )
        entry["modificatore"] = _first_non_placeholder(
            as_mapping.get("mod"),
            as_mapping.get("abilita"),
            as_mapping.get("ability_mod"),
            None,
        )
        entry["misc"] = _first_non_placeholder(as_mapping.get("misc"), None)
        if breakdown:
            entry["breakdown"] = breakdown
        if total is None and fallback_total is not None:
            if all(
                _is_placeholder(entry.get(key))
                for key in ("base", "modificatore", "misc")
            ):
                total = fallback_total
        if total is None and not all(
            _is_placeholder(entry.get(key)) for key in ("base", "modificatore", "misc")
        ):
            numeric_parts = [
                part
                for part in (
                    entry.get("base"),
                    entry.get("modificatore"),
                    entry.get("misc"),
                )
                if isinstance(part, (int, float))
            ]
            if numeric_parts:
                total = sum(numeric_parts)
        if total is None and label:
            total = _fallback_stat(label)
        if total is not None:
            entry["totale"] = total
        return entry

    def _normalize_stat_key(raw_key: object) -> str | None:
        if raw_key is None:
            return None
        key = str(raw_key).strip()
        if not key:
            return None

        alias_map = {
            "for": "FOR",
            "forza": "FOR",
            "str": "FOR",
            "des": "DES",
            "destrezza": "DES",
            "dex": "DES",
            "cos": "COS",
            "costituzione": "COS",
            "con": "COS",
            "int": "INT",
            "intelligenza": "INT",
            "sag": "SAG",
            "saggezza": "SAG",
            "wis": "SAG",
            "car": "CAR",
            "carisma": "CAR",
            "cha": "CAR",
        }

        lowered = key.lower()
        return alias_map.get(lowered, key)

    def _populate_profile_metadata(target: MutableMapping[str, object]) -> None:
        profile_sources: list[Mapping[str, object]] = []
        for candidate in (
            _as_mapping(target.get("profilo_base")),
            _as_mapping(target.get("base_profile")),
            _as_mapping(export_ctx.get("profilo_base")),
            _as_mapping(export_ctx.get("base_profile")),
            _as_mapping(payload.get("profilo_base")),
            _as_mapping(payload.get("base_profile")),
            _as_mapping(payload.get("build_state")),
            _as_mapping(payload.get("request")),
        ):
            if candidate:
                profile_sources.append(candidate)

        profile_keys: dict[str, tuple[str, ...]] = {
            "nome": ("nome", "name", "character_name"),
            "razza": ("razza", "race"),
            "allineamento": ("allineamento", "alignment"),
            "divinita": ("divinita", "deity"),
            "taglia": ("taglia", "size"),
            "eta": ("eta", "age"),
            "sesso": ("sesso", "sex", "gender"),
            "altezza": ("altezza", "height"),
            "peso": ("peso", "weight"),
            "ruolo": ("ruolo", "role", "role_hint"),
            "player_style": ("player_style",),
            "background": ("background", "background_hooks"),
        }

        for target_key, aliases in profile_keys.items():
            if not _is_placeholder(target.get(target_key)):
                continue
            values: list[object | None] = []
            for source in profile_sources:
                for alias in aliases:
                    values.append(source.get(alias))
            resolved = _first_non_placeholder(*values)
            if resolved is not None:
                target[target_key] = resolved

    def _normalize_statistics_block(*sources: Mapping | None) -> dict[str, object]:
        normalized: dict[str, object] = {}
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            for raw_key, value in source.items():
                key = _normalize_stat_key(raw_key)
                if key is None or _is_placeholder(value):
                    continue
                existing = normalized.get(key)
                if _is_placeholder(existing) or key not in normalized:
                    normalized[key] = value

        long_form_aliases = {
            "FOR": ["Forza", "forza"],
            "DES": ["Destrezza", "destrezza"],
            "COS": ["Costituzione", "costituzione"],
            "INT": ["Intelligenza", "intelligenza"],
            "SAG": ["Saggezza", "saggezza"],
            "CAR": ["Carisma", "carisma"],
        }
        for short, aliases in long_form_aliases.items():
            if short not in normalized:
                continue
            for alias in aliases:
                if alias not in normalized or _is_placeholder(normalized.get(alias)):
                    normalized[alias] = normalized[short]

        return normalized


    sheet_payload: MutableMapping[str, object] = {}
    for candidate in (
        _as_mapping(export_ctx.get("sheet_payload")),
        (
            _as_mapping(payload.get("sheet_payload"))
            if isinstance(payload, Mapping)
            else None
        ),
        _as_mapping(payload.get("sheet")) if isinstance(payload, Mapping) else None,
    ):
        if candidate:
            _merge_prefer_existing(sheet_payload, candidate)

    if ledger and "ledger" not in sheet_payload:
        sheet_payload["ledger"] = ledger

    stats_block = _normalize_statistics_block(
        _as_mapping(sheet_payload.get("statistiche")),
        _as_mapping(export_ctx.get("statistiche")),
        _as_mapping((payload.get("build_state") or {}).get("statistics")),
        _as_mapping((payload.get("benchmark") or {}).get("statistics")),
    )
    if stats_block:
        sheet_payload["statistiche"] = stats_block

    _populate_profile_metadata(sheet_payload)

    salvezze_raw = _merge_prefer_existing(
        {},
        _as_mapping(sheet_payload.get("salvezze")) or {},
        _as_mapping(export_ctx.get("salvezze")) or {},
        _as_mapping((payload.get("build_state") or {}).get("saves")) or {},
        _as_mapping((payload.get("benchmark") or {}).get("saves")) or {},
    )
    saves_breakdown = _merge_prefer_existing(
        {},
        _as_mapping(export_ctx.get("salvezze_breakdown")) or {},
        _as_mapping((payload.get("build_state") or {}).get("saves_breakdown")) or {},
    )
    normalized_saves: dict[str, object] = {}
    saves_totals: dict[str, object] = {}
    for name in ("Tempra", "Riflessi", "Volontà"):
        normalized_entry = _normalize_save_entry(
            salvezze_raw.get(name),
            _as_mapping(saves_breakdown.get(name))
            or _as_mapping(saves_breakdown.get(name.lower())),
            label=f"TS {name}",
        )
        normalized_saves[name] = normalized_entry
        saves_totals[name] = normalized_entry.get("totale")
    for extra_key, value in salvezze_raw.items():
        if extra_key in normalized_saves:
            continue
        normalized_entry = _normalize_save_entry(
            value, _as_mapping(saves_breakdown.get(extra_key))
        )
        normalized_saves[extra_key] = normalized_entry
        saves_totals[extra_key] = normalized_entry.get("totale")
    sheet_payload["salvezze_breakdown"] = normalized_saves
    if not any(
        isinstance(value, (int, float)) and value != 0
        for value in saves_totals.values()
    ):
        for key, value in list(saves_totals.items()):
            if value in {None, 0} or _is_placeholder(value):
                placeholder_label = f"TS {key}"
                saves_totals[key] = _fallback_stat(placeholder_label)
                if key in normalized_saves:
                    normalized_saves[key]["totale"] = saves_totals[key]
    sheet_payload["salvezze"] = saves_totals

    hp_block = _merge_prefer_existing(
        {},
        _as_mapping(export_ctx.get("hp")) or {},
        _as_mapping(payload.get("hp")) or {},
        _as_mapping((payload.get("build_state") or {}).get("hp")) or {},
    )
    if hp_block:
        sheet_payload["hp"] = hp_block
    pf_total = _first_non_placeholder(
        sheet_payload.get("pf_totali"),
        hp_block.get("totale") if hp_block else None,
        hp_block.get("total") if hp_block else None,
        hp_block.get("hp_total") if hp_block else None,
        (
            (sheet_payload.get("statistiche_chiave") or {}).get("PF")
            if isinstance(sheet_payload.get("statistiche_chiave"), Mapping)
            else None
        ),
    )
    if isinstance(pf_total, (int, float)) and pf_total == 0:
        pf_total = None
    if pf_total is not None:
        sheet_payload["pf_totali"] = pf_total
    elif hp_block:
        sheet_payload["pf_totali"] = hp_block.get("totale") or _fallback_stat(
            "PF totali"
        )
    else:
        sheet_payload["pf_totali"] = _fallback_stat("PF totali")
    pf_progression = _first_non_placeholder(
        sheet_payload.get("pf_per_livello"),
        hp_block.get("per_livello") if hp_block else None,
        hp_block.get("per_level") if hp_block else None,
        hp_block.get("progressione") if hp_block else None,
    )
    if pf_progression is not None:
        sheet_payload["pf_per_livello"] = pf_progression
    elif sheet_payload.get("pf_totali"):
        sheet_payload.setdefault(
            "pf_per_livello",
            _fallback_stat("PF per livello"),
        )

    derived_core = _as_mapping(export_ctx.get("derived")) or _as_mapping(
        (payload.get("build_state") or {}).get("derived")
    )
    derived_core = derived_core or _as_mapping((derived_core or {}).get("core")) or {}

    ac_breakdown = _merge_prefer_existing(
        {},
        _as_mapping(sheet_payload.get("ac_breakdown")) or {},
        _as_mapping(export_ctx.get("ac_breakdown")) or {},
        _as_mapping((payload.get("build_state") or {}).get("ac")) or {},
        _as_mapping((derived_core or {}).get("ac")) or {},
    )
    if ac_breakdown:
        sheet_payload["ac_breakdown"] = ac_breakdown
    stat_key_block = _as_mapping(sheet_payload.get("statistiche_chiave")) or {}
    ac_defaults = {
        "AC_arm": 0,
        "AC_scudo": 0,
        "AC_des": 0,
        "AC_defl": 0,
        "AC_nat": 0,
        "AC_dodge": 0,
        "AC_misc": 0,
    }
    for ac_key, default in ac_defaults.items():
        value = _first_non_placeholder(
            sheet_payload.get(ac_key),
            ac_breakdown.get(ac_key) if ac_breakdown else None,
        )
        if value is None:
            value = default
        sheet_payload[ac_key] = value
    ac_base = _first_non_placeholder(
        sheet_payload.get("AC_base"),
        ac_breakdown.get("AC_base") if ac_breakdown else None,
        10,
    )
    if ac_base is not None:
        sheet_payload["AC_base"] = ac_base
    for ca_key in ("AC_tot", "CA_touch", "CA_ff"):
        derived = _first_non_placeholder(
            ac_breakdown.get(ca_key) if ac_breakdown else None,
            (
                stat_key_block.get(ca_key.lower())
                if isinstance(stat_key_block.get(ca_key.lower()), (int, float))
                else None
            ),
            stat_key_block.get(ca_key),
            stat_key_block.get("ca") if ca_key == "AC_tot" else None,
            sheet_payload.get(ca_key),
        )
        existing_value = sheet_payload.get(ca_key)
        if derived is not None and (
            ca_key not in sheet_payload
            or _is_placeholder(existing_value)
            or ((not ac_breakdown) and existing_value in {0, 10})
        ):
            sheet_payload[ca_key] = derived

    if "AC_tot" not in sheet_payload:
        sheet_payload["AC_tot"] = ac_base + sum(
            sheet_payload.get(ac_key, 0) for ac_key in ac_defaults
        )
    if sheet_payload.get("AC_tot") in {None, 0}:
        sheet_payload["AC_tot"] = _fallback_stat("CA totale")
    if "CA_touch" not in sheet_payload:
        sheet_payload["CA_touch"] = (
            ac_base
            + sheet_payload.get("AC_des", 0)
            + sheet_payload.get("AC_defl", 0)
            + sheet_payload.get("AC_dodge", 0)
            + sheet_payload.get("AC_misc", 0)
        )
    if "CA_ff" not in sheet_payload:
        sheet_payload["CA_ff"] = (
            ac_base
            + sheet_payload.get("AC_arm", 0)
            + sheet_payload.get("AC_scudo", 0)
            + sheet_payload.get("AC_nat", 0)
            + sheet_payload.get("AC_defl", 0)
            + sheet_payload.get("AC_misc", 0)
        )

    bab = _first_non_placeholder(
        sheet_payload.get("BAB"),
        export_ctx.get("BAB") or export_ctx.get("bab"),
        (payload.get("build_state") or {}).get("bab"),
        (payload.get("benchmark") or {}).get("bab"),
        (derived_core or {}).get("bab_total"),
        (derived_core or {}).get("bab_base"),
    )
    if bab is None:
        sheet_payload["BAB"] = _fallback_stat("BAB")
    else:
        sheet_payload["BAB"] = bab

    initiative = _first_non_placeholder(
        sheet_payload.get("iniziativa"),
        export_ctx.get("iniziativa"),
        stat_key_block.get("iniziativa"),
        stat_key_block.get("init"),
        (payload.get("build_state") or {}).get("initiative"),
        (payload.get("benchmark") or {}).get("initiative"),
        (derived_core or {}).get("initiative_mod"),
        (derived_core or {}).get("initiative_total"),
    )
    if initiative is not None:
        sheet_payload["iniziativa"] = initiative
        if _is_placeholder(sheet_payload.get("init")):
            sheet_payload["init"] = initiative

    speed = _first_non_placeholder(
        sheet_payload.get("velocita"),
        export_ctx.get("velocita") or export_ctx.get("speed"),
        stat_key_block.get("velocita"),
        stat_key_block.get("speed"),
        (payload.get("build_state") or {}).get("speed"),
        (derived_core or {}).get("speed_total"),
        (derived_core or {}).get("speed_base"),
    )
    if speed is not None:
        sheet_payload["velocita"] = speed
        if _is_placeholder(sheet_payload.get("speed")):
            sheet_payload["speed"] = speed

    skill_points = _first_non_placeholder(
        sheet_payload.get("skill_points"),
        (payload.get("build_state") or {}).get("skill_points"),
        (payload.get("benchmark") or {}).get("skill_points"),
    )
    if skill_points is not None:
        sheet_payload["skill_points"] = skill_points

    skills_map = _merge_prefer_existing(
        {},
        _as_mapping(sheet_payload.get("skills_map")) or {},
        _as_mapping(export_ctx.get("skills_map")) or {},
        _as_mapping((payload.get("build_state") or {}).get("skills_map")) or {},
        _as_mapping((derived_core or {}).get("skills_by_name")) or {},
    )
    if skills_map:
        sheet_payload["skills_map"] = skills_map

    skills_list = _merge_unique_list(
        sheet_payload.get("skills"),
        export_ctx.get("skills"),
        (payload.get("build_state") or {}).get("skills"),
    )
    if skills_list:
        sheet_payload["skills"] = skills_list

    feats = _merge_unique_list(
        sheet_payload.get("talenti"),
        export_ctx.get("talenti"),
        (payload.get("build_state") or {}).get("feats"),
        [
            p.get("talento")
            for p in sheet_payload.get("progressione", [])
            if isinstance(p, Mapping) and p.get("talento")
        ],
    )
    if feats:
        sheet_payload["talenti"] = feats

    class_features = _merge_unique_list(
        sheet_payload.get("capacita_classe"),
        export_ctx.get("capacita_classe"),
        (payload.get("build_state") or {}).get("class_features"),
        [
            priv
            for entry in sheet_payload.get("progressione", [])
            if isinstance(entry, Mapping)
            for priv in (
                entry.get("privilegi")
                if isinstance(entry.get("privilegi"), Sequence)
                and not isinstance(entry.get("privilegi"), (str, bytes))
                else [entry.get("privilegi")]
            )
            if priv
        ],
    )
    if class_features:
        sheet_payload["capacita_classe"] = class_features

    progression = _merge_unique_list(
        sheet_payload.get("progressione"),
        export_ctx.get("progressione") or export_ctx.get("progression"),
        payload.get("progressione") if isinstance(payload, Mapping) else None,
        (payload.get("build_state") or {}).get("progression"),
    )
    if progression:
        sheet_payload["progressione"] = progression

    equip_list = _merge_unique_list(
        sheet_payload.get("equipaggiamento"),
        export_ctx.get("equipaggiamento"),
        (
            (payload.get("ledger") or {}).get("equipaggiamento")
            if isinstance(payload.get("ledger"), Mapping)
            else None
        ),
    )
    if equip_list:
        sheet_payload["equipaggiamento"] = equip_list

    equipment_summary = _merge_prefer_existing(
        {},
        _as_mapping(sheet_payload.get("equipment_summary")) or {},
        _as_mapping(export_ctx.get("equipment_summary")) or {},
        (
            _as_mapping((payload.get("ledger") or {}).get("equipment_summary"))
            if isinstance(payload.get("ledger"), Mapping)
            else {}
        ),
    )
    if equipment_summary:
        sheet_payload["equipment_summary"] = equipment_summary

    inventory = _merge_unique_list(
        sheet_payload.get("inventario"),
        export_ctx.get("inventario"),
        (
            (payload.get("ledger") or {}).get("inventario")
            if isinstance(payload.get("ledger"), Mapping)
            else None
        ),
    )
    if inventory:
        sheet_payload["inventario"] = inventory

    spell_levels = _merge_unique_list(
        sheet_payload.get("spell_levels"),
        export_ctx.get("spell_levels"),
    )
    if spell_levels:
        sheet_payload["spell_levels"] = spell_levels

    magic_map = _merge_prefer_existing(
        {},
        _as_mapping(sheet_payload.get("magia")) or {},
        _as_mapping(export_ctx.get("magia")) or {},
        _as_mapping((payload.get("build_state") or {}).get("magia")) or {},
    )

    spell_list = _merge_prefer_existing(
        {},
        _as_mapping(magic_map.get("spell_list")) or {},
        _as_mapping(export_ctx.get("spell_list")) or {},
        _as_mapping((payload.get("build_state") or {}).get("spell_list")) or {},
    )
    if spell_list:
        magic_map["spell_list"] = spell_list

    spells_prepared = _merge_prefer_existing(
        {},
        _as_mapping(magic_map.get("spells_prepared")) or {},
        _as_mapping(export_ctx.get("spells_prepared")) or {},
        _as_mapping((payload.get("build_state") or {}).get("spells_prepared")) or {},
    )
    if spells_prepared:
        magic_map["spells_prepared"] = spells_prepared

    slots_per_day = _merge_prefer_existing(
        {},
        _as_mapping(magic_map.get("slots_per_day")) or {},
        _as_mapping(export_ctx.get("slots_per_day")) or {},
        _as_mapping((payload.get("build_state") or {}).get("slots_per_day")) or {},
        _as_mapping((payload.get("build_state") or {}).get("spell_slots")) or {},
    )
    if not slots_per_day and spell_levels:
        slots_per_day = {str(level): 0 for level in spell_levels}
    if slots_per_day:
        magic_map["slots_per_day"] = slots_per_day

    if magic_map:
        sheet_payload["magia"] = magic_map

    slot_text = _first_non_placeholder(
        sheet_payload.get("slot_incantesimi"), export_ctx.get("slot_incantesimi")
    )
    if slot_text is not None:
        sheet_payload["slot_incantesimi"] = slot_text

    languages = _merge_unique_list(
        sheet_payload.get("lingue"),
        export_ctx.get("lingue"),
        (payload.get("build_state") or {}).get("languages"),
    )
    if languages:
        sheet_payload["lingue"] = languages

    senses = _merge_unique_list(
        sheet_payload.get("sensi"),
        export_ctx.get("sensi"),
        (payload.get("build_state") or {}).get("senses"),
    )
    if senses:
        sheet_payload["sensi"] = senses

    conditions = _merge_unique_list(
        sheet_payload.get("condizioni"),
        export_ctx.get("condizioni"),
        (payload.get("build_state") or {}).get("conditions"),
    )
    if conditions:
        sheet_payload["condizioni"] = conditions

    module_payloads = _merge_prefer_existing(
        {},
        _as_mapping(sheet_payload.get("modules")) or {},
        _as_mapping(export_ctx.get("modules")) or {},
        _as_mapping(payload.get("modules")) or {},
        _load_local_modules(SHEET_MODULE_TARGETS),
    )

    allowed_sheet_modules = {
        name: module_payloads.get(name) for name in SHEET_MODULE_TARGETS
    }
    filtered_modules = {k: v for k, v in allowed_sheet_modules.items() if v}

    if filtered_modules:
        sheet_payload["modules"] = filtered_modules

    rendered_sheet = None
    template_source = allowed_sheet_modules.get("scheda_pg_markdown_template.md")
    if template_source:
        try:
            rendered_sheet = _render_sheet_template(template_source, sheet_payload)
        except Exception as exc:  # pragma: no cover - defensive
            error_message = f"Rendering scheda_pg_markdown_template.md fallita: {exc}"
            logging.warning(error_message)
            sheet_payload["sheet_render_error"] = error_message

    if rendered_sheet:
        rendered_sheet = textwrap.dedent(rendered_sheet).strip()
        if rendered_sheet:
            sheet_payload["sheet_markdown"] = rendered_sheet

    sources = _merge_unique_list(
        sheet_payload.get("fonti"), [source_url] if source_url else []
    )
    if sources:
        sheet_payload["fonti"] = sources

    sheet_payload.setdefault("print_mode", False)
    sheet_payload.setdefault("show_minmax", True)
    sheet_payload.setdefault("show_vtt", True)
    sheet_payload.setdefault("show_qa", True)
    sheet_payload.setdefault("show_explain", True)
    sheet_payload.setdefault("show_ledger", True)
    sheet_payload.setdefault("decimal_comma", True)
    sheet_payload.setdefault("salvezze", {})
    sheet_payload.setdefault("skills_map", {})
    sheet_payload.setdefault("skills", [])
    sheet_payload.setdefault("spell_levels", [])
    sheet_payload.setdefault("magia", {})
    sheet_payload.setdefault("lingue", [])
    sheet_payload.setdefault("sensi", [])
    sheet_payload.setdefault("condizioni", [])
    sheet_payload.setdefault("equipaggiamento", [])
    sheet_payload.setdefault("inventario", [])
    sheet_payload.setdefault("talenti", [])
    sheet_payload.setdefault("capacita_classe", [])
    sheet_payload.setdefault("progressione", [])
    sheet_payload.setdefault("velocita", 0)
    sheet_payload.setdefault("iniziativa", 0)
    sheet_payload.setdefault("pf_totali", 0)
    sheet_payload.setdefault("skill_points", 0)

    return sheet_payload

def _stringify_sequence(values: object, *, limit: int | None = None) -> list[str]:
    """Converti una sequenza generica in un elenco di stringhe pulite."""

    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []

    normalized: list[str] = []
    for item in values:
        if isinstance(item, Mapping):
            candidate = item.get("name") or item.get("label") or item.get("id")
            normalized.append(str(candidate)) if candidate else None
        else:
            normalized.append(str(item))

        if limit is not None and len(normalized) >= limit:
            break

    return [value.strip() for value in normalized if value and value.strip()]


def _normalize_badge_value(badge: object) -> str | None:
    if isinstance(badge, str):
        return badge.strip().lower() or None
    if isinstance(badge, Mapping):
        for key in ("label", "value", "badge"):
            candidate = badge.get(key)
            if isinstance(candidate, str):
                return candidate.strip().lower() or None
    return None


def _ruling_context_from_payload(
    payload: Mapping[str, Any], request: BuildRequest
) -> Mapping[str, object]:
    export = payload.get("export") if isinstance(payload, Mapping) else None
    sheet_payload = (
        export.get("sheet_payload") if isinstance(export, Mapping) else None
    )
    talents = []
    if isinstance(sheet_payload, Mapping):
        talents = _stringify_sequence(sheet_payload.get("talenti"), limit=5)

    hr_sources: object | None = None
    meta_sources: object | None = None
    pfs_mode: object | None = None
    if isinstance(sheet_payload, Mapping):
        hr_sources = sheet_payload.get("hr_sources")
        meta_sources = sheet_payload.get("meta_sources")
        pfs_mode = sheet_payload.get("pfs_mode")

    return {
        "class": payload.get("class") or request.class_name,
        "level": payload.get("request", {}).get("level") or request.level,
        "talenti_chiave": talents,
        "hr_sources": hr_sources,
        "meta_sources": meta_sources,
        "pfs_mode": pfs_mode,
    }


def _pfs_blocks_homebrew(context: Mapping[str, object]) -> bool:
    pfs_mode = str(context.get("pfs_mode") or "").lower()
    pfs_active = pfs_mode in {"true", "on", "yes", "1", "active", "pfs"}
    hr_present = bool(context.get("hr_sources"))
    meta_present = bool(context.get("meta_sources"))
    return bool(pfs_active and (hr_present or meta_present))


async def _validate_ruling_badge(
    client: httpx.AsyncClient,
    *,
    url: str | None,
    api_key: str | None,
    payload: MutableMapping,
    request: BuildRequest,
    timeout: float,
    max_retries: int,
) -> tuple[str, object | None]:
    if not url:
        raise BuildFetchError("Endpoint Ruling Expert obbligatorio per il salvataggio")

    context = _ruling_context_from_payload(payload, request)

    if _pfs_blocks_homebrew(context):
        raise BuildFetchError(
            "PFS attivo: HR/META rilevati e non ammessi per lo snapshot",
        )

    headers = {"x-api-key": api_key} if api_key else {}
    response = await request_with_retry(
        client,
        "POST",
        url,
        headers=headers,
        json_body={"build": payload, "context": context},
        timeout=timeout,
        max_retries=max_retries,
        backoff_factor=0.5,
    )

    try:
        data = response.json()
    except json.JSONDecodeError as exc:  # pragma: no cover - network dependent
        raise BuildFetchError("Risposta Ruling Expert non JSON") from exc

    violations = data.get("violations") if isinstance(data, Mapping) else None
    if violations:
        raise BuildFetchError(
            "Violazioni Ruling Expert: " + "; ".join(map(str, violations))
        )

    badge = data.get("ruling_badge") if isinstance(data, Mapping) else None
    badge = badge or (data.get("badge") if isinstance(data, Mapping) else None)
    normalized_badge = _normalize_badge_value(badge)
    if not normalized_badge:
        raise BuildFetchError("Badge Ruling Expert mancante o non conforme")

    sources = data.get("sources") if isinstance(data, Mapping) else None
    sources = sources or (data.get("fonti") if isinstance(data, Mapping) else None)

    payload["ruling_badge"] = normalized_badge
    if sources:
        payload["ruling_sources"] = sources
    payload.setdefault("qa", {})["ruling_expert"] = {
        "badge": normalized_badge,
        "sources": sources,
        "context": context,
    }

    return normalized_badge, sources



def _apply_level_checkpoint(
    payload: MutableMapping[str, object], target_level: int | None
) -> None:
    if target_level is None:
        return

    export_ctx = payload.get("export") if isinstance(payload, Mapping) else None
    sheet_payload = None
    if isinstance(export_ctx, Mapping):
        sheet_payload = export_ctx.get("sheet_payload")
    if sheet_payload is None and isinstance(payload.get("sheet_payload"), Mapping):
        sheet_payload = payload.get("sheet_payload")

    if not isinstance(sheet_payload, MutableMapping):
        return

    truncated_progression = _truncate_sequence_by_level(
        sheet_payload.get("progressione"), target_level
    )
    if truncated_progression is not None:
        sheet_payload["progressione"] = truncated_progression

        notes = sheet_payload.get("note_progressione")
        if isinstance(notes, Sequence) and not isinstance(notes, (str, bytes)):
            sheet_payload["note_progressione"] = list(notes)[
                : len(truncated_progression)
            ]

    for key in ("magia", "equipaggiamento"):
        truncated = _truncate_sequence_by_level(sheet_payload.get(key), target_level)
        if truncated is not None:
            sheet_payload[key] = truncated


def _progression_level_errors(
    sheet_payload: Mapping[str, object] | None, target_level: int | None
) -> list[str]:
    if not target_level or target_level < 1:
        return []

    if not isinstance(sheet_payload, Mapping):
        return []

    progression = sheet_payload.get("progressione")
    progression_entries: Sequence | None = None
    if isinstance(progression, Sequence) and not isinstance(progression, (str, bytes)):
        progression_entries = progression

    has_progression_content = False
    if progression_entries:
        for candidate in progression_entries:
            if _has_content(candidate):
                has_progression_content = True
                break

    if not has_progression_content:
        return []

    def _entry_for_level(level: int) -> Mapping | None:
        if progression_entries is None:
            return None

        for candidate in progression_entries:
            if isinstance(candidate, Mapping) and candidate.get("livello") == level:
                return candidate

        if 0 <= level - 1 < len(progression_entries):
            candidate = progression_entries[level - 1]
            if isinstance(candidate, Mapping):
                return candidate
        return None

    errors: list[str] = []
    for level in range(1, target_level + 1):
        progression_entry = _entry_for_level(level)
        privileges = None
        feats = None
        if isinstance(progression_entry, Mapping):
            privileges = progression_entry.get("privilegi")
            feats = progression_entry.get("talenti") or progression_entry.get("talento")

        has_progression = _has_content(privileges) or _has_content(feats)
        has_core_blocks = all(
            _has_content(value)
            for value in (
                sheet_payload.get("pf_totali") or sheet_payload.get("hp"),
                sheet_payload.get("salvezze"),
                sheet_payload.get("skills_map") or sheet_payload.get("skills"),
                sheet_payload.get("skill_points"),
                sheet_payload.get("equipaggiamento") or sheet_payload.get("inventario"),
                sheet_payload.get("spell_levels")
                or sheet_payload.get("magia")
                or sheet_payload.get("slot_incantesimi"),
                sheet_payload.get("ac_breakdown"),
                sheet_payload.get("iniziativa") or sheet_payload.get("velocita"),
            )
        )

        if not (has_progression and has_core_blocks):
            errors.append(f"Progressione assente al livello {level}")

    return errors


async def fetch_build(
    client: httpx.AsyncClient,
    api_key: str | None,
    request: BuildRequest,
    max_retries: int,
    require_complete: bool = True,
    target_level: int | None = None,
    ruling_expert_url: str | None = None,
    ruling_timeout: float = 30.0,
    ruling_max_retries: int | None = None,
) -> MutableMapping:
    params: MutableMapping[str, object] = {
        "mode": request.mode,
        "class": request.class_name,
        "stub": True,
    }
    if target_level is not None:
        params["level"] = target_level
    params.update(request.query_params)
    headers = {"x-api-key": api_key} if api_key else {}
    method = request.http_method()
    response = await request_with_retry(
        client,
        method,
        MODULE_ENDPOINT,
        params=params,
        headers=headers,
        timeout=60,
        max_retries=max_retries,
        json_body=request.body_params or None,
    )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:  # pragma: no cover - network dependent
        raise BuildFetchError(
            f"Risposta non JSON per {request.class_name}: {exc}"
        ) from exc

    for required in ("build_state", "benchmark", "export"):
        if required not in payload:
            raise BuildFetchError(
                f"Campo '{required}' mancante nella risposta per {request.class_name}. Chiavi viste: {sorted(payload.keys())}"
            )

    sheet = None
    for candidate in (
        "sheet",
        "sheet_markup",
        "sheet_markdown",
        "sheet_markdown_template",
    ):
        if candidate in payload:
            sheet = payload[candidate]
            break

    narrative = payload.get("narrative")
    ledger = payload.get("ledger") or payload.get("adventurer_ledger")

    build_state = payload.get("build_state") or {}
    normalized_mode = normalize_mode(request.mode)
    expected_step_total = expected_step_total_for_mode(normalized_mode)
    observed_step_total = build_state.get("step_total")
    step_labels = (
        build_state.get("step_labels") if isinstance(build_state, Mapping) else None
    )
    step_labels_count = len(step_labels) if isinstance(step_labels, Mapping) else None
    has_extended_steps = bool(step_labels_count and step_labels_count >= 16)
    if observed_step_total is None:
        logging.warning(
            "Risposta per %s (mode=%s) priva di step_total: impossibile verificare il flow",
            request.class_name,
            normalized_mode,
        )
    elif observed_step_total != expected_step_total:
        logging.warning(
            "Step total inatteso per %s (mode=%s): visto %s, atteso %s",
            request.class_name,
            normalized_mode,
            observed_step_total,
            expected_step_total,
        )
    else:
        logging.info(
            "Modalità %s confermata per %s: step_total=%s (%s step disponibili)",
            normalized_mode,
            request.class_name,
            observed_step_total,
            "16" if normalized_mode == "extended" else "8",
        )

    if request.race is None and build_state.get("race"):
        request.race = build_state.get("race")
    if request.archetype is None and build_state.get("archetype"):
        request.archetype = build_state.get("archetype")
    if request.background is None and request.body_params.get("background_hooks"):
        request.background = str(request.body_params.get("background_hooks"))

    composite = {
        "build": {
            "build_state": payload.get("build_state"),
            "benchmark": payload.get("benchmark"),
            "export": payload.get("export"),
        },
    }
    if narrative is not None:
        composite["narrative"] = narrative
    if sheet is not None:
        composite["sheet"] = sheet
    if ledger is not None:
        composite["ledger"] = ledger

    completeness_errors: list[str] = []
    statistics = (build_state or {}).get("statistics") or (
        payload.get("benchmark") or {}
    ).get("statistics")
    if not statistics or (
        isinstance(statistics, Mapping) and not any(statistics.values())
    ):
        completeness_errors.append("Statistiche mancanti o vuote")

    if not narrative:
        completeness_errors.append("Narrativa assente")
    else:

        def _contains_stub(value: object) -> bool:
            if isinstance(value, str):
                return "stub" in value.lower()
            if isinstance(value, Mapping):
                return any(_contains_stub(v) for v in value.values())
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return any(_contains_stub(v) for v in value)
            return False

        if _contains_stub(narrative):
            completeness_errors.append("Narrativa contiene placeholder 'stub'")

    if not ledger or (isinstance(ledger, Mapping) and not any(ledger.values())):
        completeness_errors.append("Ledger assente o senza contenuti")
    source_url = str(response.url)
    export_ctx = payload.setdefault("export", {})
    sheet_payload = _enrich_sheet_payload(
        payload, ledger if isinstance(ledger, Mapping) else None, source_url
    )
    export_ctx["sheet_payload"] = sheet_payload
    sheet_markdown = sheet_payload.get("sheet_markdown")
    if isinstance(sheet_markdown, str):
        payload["sheet"] = sheet_markdown
        composite["sheet"] = sheet_markdown
    elif sheet is not None:
        composite.setdefault("sheet", sheet)

    def _require_block(label: str, *values: object) -> None:
        if not any(_has_content(value) for value in values):
            completeness_errors.append(label)

    _require_block(
        "PF mancanti o vuoti", sheet_payload.get("pf_totali"), sheet_payload.get("hp")
    )
    _require_block("Salvezze mancanti o vuote", sheet_payload.get("salvezze"))
    _require_block(
        "Skill assenti o vuote",
        sheet_payload.get("skills_map"),
        sheet_payload.get("skills"),
        sheet_payload.get("skill_points"),
    )
    _require_block(
        "Talenti/capacità mancanti o vuote",
        sheet_payload.get("talenti"),
        sheet_payload.get("capacita_classe"),
    )
    _require_block(
        "Equipaggiamento/inventario mancante o vuoto",
        sheet_payload.get("equipaggiamento"),
        sheet_payload.get("inventario"),
    )
    _require_block(
        "Sezione incantesimi mancante o vuota",
        sheet_payload.get("spell_levels"),
        sheet_payload.get("magia"),
        sheet_payload.get("slot_incantesimi"),
    )
    _require_block("CA dettagliata mancante o vuota", sheet_payload.get("ac_breakdown"))
    _require_block(
        "Iniziativa o velocità mancanti",
        sheet_payload.get("iniziativa"),
        sheet_payload.get("velocita"),
    )

    progression_errors = _progression_level_errors(sheet_payload, target_level)
    for error in progression_errors:
        if error not in completeness_errors:
            completeness_errors.append(error)

    payload.update(
        {
            "class": request.class_name,
            "mode": request.mode,
            "source_url": source_url,
            "fetched_at": now_iso_utc(),
            "request": request.metadata(),
            "composite": composite,
            "query_params": params,
            "body_params": request.body_params,
            "mode_normalized": normalized_mode,
            "step_audit": {
                "normalized_mode": normalized_mode,
                "expected_step_total": expected_step_total,
                "observed_step_total": observed_step_total,
                "step_total_ok": observed_step_total == expected_step_total,
                "step_labels_count": step_labels_count,
                "has_extended_steps": has_extended_steps,
            },
            "completeness": {
                "errors": completeness_errors,
                "require_complete": require_complete,
            },
        }
    )

    ruling_retries = ruling_max_retries if ruling_max_retries is not None else max_retries
    await _validate_ruling_badge(
        client,
        url=ruling_expert_url,
        api_key=api_key,
        payload=payload,
        request=request,
        timeout=ruling_timeout,
        max_retries=ruling_retries,
    )

    if require_complete and completeness_errors:
        joined_errors = "; ".join(completeness_errors)
        raise BuildFetchError(
            f"Build incompleta per {request.class_name}: {joined_errors}",
            completeness_errors=completeness_errors,
        )
    return payload


async def fetch_module(
    client: httpx.AsyncClient, api_key: str | None, module_name: str, max_retries: int
) -> tuple[str, Mapping]:
    headers = {"x-api-key": api_key} if api_key else {}
    content_resp = await request_with_retry(
        client,
        "GET",
        MODULE_DUMP_ENDPOINT.format(name=module_name),
        headers=headers,
        timeout=60,
        max_retries=max_retries,
        backoff_factor=0.5,
    )

    meta_resp = await request_with_retry(
        client,
        "GET",
        MODULE_META_ENDPOINT.format(name=module_name),
        headers=headers,
        timeout=30,
        max_retries=max_retries,
        backoff_factor=0.5,
    )

    return content_resp.text, meta_resp.json()


async def discover_modules(
    client: httpx.AsyncClient, api_key: str | None, max_retries: int
) -> list[str]:
    headers = {"x-api-key": api_key} if api_key else {}
    response = await request_with_retry(
        client,
        "GET",
        MODULE_LIST_ENDPOINT,
        headers=headers,
        timeout=30,
        max_retries=max_retries,
        backoff_factor=0.5,
    )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:  # pragma: no cover - network dependent
        raise ValueError("Risposta /modules non valida (JSON)") from exc

    if isinstance(payload, Mapping) and "modules" in payload:
        payload = payload.get("modules")

    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        raise ValueError(f"Formato /modules inatteso: {payload!r}")

    names: list[str] = []
    for item in payload:
        if isinstance(item, Mapping):
            name = item.get("name")
        else:
            name = item
        if not name:
            continue
        names.append(str(name))

    return names


def write_json(path: Path, data: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def path_with_suffix(path: Path, suffix: str) -> Path:
    return path.with_name(f"{path.stem}.{suffix}{path.suffix}")


def analyze_indices(
    build_index_path: Path,
    module_index_path: Path,
    *,
    archive_dir: Path | None = None,
) -> Mapping[str, Any]:
    def _load_index(path: Path) -> Mapping[str, Any]:
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - defensive logging
                logging.warning("Impossibile leggere l'indice %s: %s", path, exc)
        return {"entries": []}

    def _archive_payload(
        source: Path, destination_dir: Path, archived: list[str]
    ) -> None:
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / source.name
        if destination.exists():
            destination = destination_dir / f"{source.stem}_copy{destination.suffix}"
        shutil.copy2(source, destination)
        archived.append(str(destination))

    build_index_payload = _load_index(build_index_path)
    module_index_payload = _load_index(module_index_path)

    build_entries: Sequence[Mapping[str, object]] = (
        build_index_payload.get("entries") or []
    )
    module_entries: Sequence[Mapping[str, object]] = (
        module_index_payload.get("entries") or []
    )

    build_stats = {"total": 0, "ok": 0, "invalid": 0, "errors": 0}
    module_stats = {"total": 0, "ok": 0, "invalid": 0, "errors": 0}
    invalid_builds: list[Mapping[str, object]] = []
    invalid_modules: list[Mapping[str, object]] = []
    archived_files: list[str] = []

    for entry in build_entries:
        status = str(entry.get("status") or "error")
        build_stats["total"] += 1
        if status == "ok":
            build_stats["ok"] += 1
            continue
        if status == "invalid":
            build_stats["invalid"] += 1
        else:
            build_stats["errors"] += 1
        invalid_builds.append(entry)
        file_path = entry.get("file")
        if archive_dir and file_path:
            source = Path(str(file_path))
            if source.exists():
                _archive_payload(source, archive_dir / "builds", archived_files)

    for entry in module_entries:
        status = str(entry.get("status") or "error")
        module_stats["total"] += 1
        if status == "ok":
            module_stats["ok"] += 1
            continue
        if status == "invalid":
            module_stats["invalid"] += 1
        else:
            module_stats["errors"] += 1
        invalid_modules.append(entry)
        file_path = entry.get("file")
        if archive_dir and file_path:
            source = Path(str(file_path))
            if source.exists():
                _archive_payload(source, archive_dir / "modules", archived_files)

    report = {
        "generated_at": now_iso_utc(),
        "build_index": str(build_index_path),
        "module_index": str(module_index_path),
        "builds": {
            **build_stats,
            "invalid_entries": invalid_builds,
        },
        "modules": {
            **module_stats,
            "invalid_entries": invalid_modules,
        },
        "archived_files": archived_files,
    }

    return report


def build_index_entry(
    request: BuildRequest,
    output_file: Path | None,
    status: str,
    error: str | None = None,
    step_audit: Mapping[str, object] | None = None,
    completeness_errors: Sequence[str] | None = None,
    ruling_badge: str | None = None,
    ruling_sources: object | None = None,
) -> Mapping:
    entry: dict[str, object] = {
        "file": str(output_file) if output_file else None,
        "status": status,
        "output_prefix": request.output_name(),
        "level": request.level,
        **request.metadata(),
    }
    if error:
        entry["error"] = error
    if completeness_errors:
        entry["completeness_errors"] = list(completeness_errors)
    if ruling_badge:
        entry["ruling_badge"] = ruling_badge
    if ruling_sources:
        entry["ruling_sources"] = ruling_sources
    if step_audit:
        entry.update(
            {
                "step_total": step_audit.get("observed_step_total"),
                "expected_step_total": step_audit.get("expected_step_total"),
                "mode_normalized": step_audit.get("normalized_mode"),
                "extended_steps_available": step_audit.get("has_extended_steps"),
                "step_total_ok": step_audit.get("step_total_ok"),
            }
        )
    return entry


def module_index_entry(
    name: str,
    output_file: Path | None,
    status: str,
    meta: Mapping | None = None,
    error: str | None = None,
) -> Mapping:
    entry: dict[str, object] = {
        "module": name,
        "file": str(output_file) if output_file else None,
        "status": status,
    }
    if meta:
        entry["meta"] = meta
    if error:
        entry["error"] = error
    return entry


async def run_harvest(
    requests: Iterable[BuildRequest],
    api_url: str,
    api_key: str | None,
    output_dir: Path,
    index_path: Path,
    modules: Sequence[str],
    modules_output_dir: Path,
    module_index_path: Path,
    concurrency: int,
    max_retries: int,
    spec_path: Path | None = None,
    discover: bool = False,
    include_filters: Sequence[str] | None = None,
    exclude_filters: Sequence[str] | None = None,
    strict: bool = False,
    keep_invalid: bool = False,
    require_complete: bool = True,
    skip_health_check: bool = False,
    level_filters: Sequence[int] | None = None,
    skip_unchanged: bool = False,
    max_items: int | None = None,
    ruling_expert_url: str | None = None,
    ruling_timeout: float = 30.0,
    ruling_max_retries: int | None = None,
) -> None:
    requests = list(requests)
    max_items = int(max_items) if max_items is not None else None
    max_items = max_items if max_items and max_items > 0 else None
    ensure_output_dirs(output_dir)
    ensure_output_dirs(modules_output_dir)
    builds_index: dict[str, object] = {
        "generated_at": now_iso_utc(),
        "api_url": api_url,
        "mode": (
            requests[0].mode
            if requests and len({req.mode for req in requests}) == 1
            else "mixed" if requests else "mixed"
        ),
        "spec_file": str(spec_path) if spec_path else None,
        "entries": [],
    }
    modules_index: dict[str, object] = {
        "generated_at": now_iso_utc(),
        "api_url": api_url,
        "entries": [],
    }

    existing_module_entries: dict[str, Mapping] = {}
    if module_index_path.is_file():
        try:
            cached = json.loads(module_index_path.read_text(encoding="utf-8"))
            for entry in cached.get("entries", []):
                name = entry.get("module")
                if name:
                    existing_module_entries[str(name)] = entry
        except Exception as exc:  # pragma: no cover - defensive logging only
            logging.warning(
                "Impossibile caricare module_index esistente %s: %s",
                module_index_path,
                exc,
            )

    include_filters = include_filters or []
    exclude_filters = exclude_filters or []
    discovery_info: Mapping[str, object] | None = None

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async with httpx.AsyncClient(
        base_url=api_url.rstrip("/"), follow_redirects=True
    ) as client:
        if skip_health_check:
            logging.warning("Salto il controllo di health check richiesto dall'utente")
        else:
            await assert_api_reachable(client, api_key)
        if discover:
            discovered = await discover_modules(client, api_key, max_retries)
            filtered_discovered = apply_glob_filters(
                discovered, include_filters, exclude_filters
            )
            discovery_info = {
                "performed_at": now_iso_utc(),
                "include_filters": list(include_filters),
                "exclude_filters": list(exclude_filters),
                "raw": sorted(discovered),
                "raw_count": len(discovered),
                "selected": sorted(filtered_discovered),
            }
        else:
            filtered_discovered = []

        module_plan: list[str] = []
        seen: set[str] = set()
        for name in modules:
            if name not in seen:
                module_plan.append(name)
                seen.add(name)
        for name in sorted(filtered_discovered):
            if name not in seen:
                module_plan.append(name)
                seen.add(name)

        modules_index["module_plan"] = module_plan

        level_filter_set = (
            {int(level) for level in level_filters} if level_filters else None
        )

        build_tasks = []
        snapshots_planned = 0
        skipped_for_limit = 0
        limit_reached = False
        for build_request in requests:
            if limit_reached:
                break
            seen_levels: set[int] = set()
            level_plan: list[int] = []
            levels_to_process = [1, *build_request.level_checkpoints]

            for level in levels_to_process:
                try:
                    coerced = int(level)
                except (TypeError, ValueError):
                    continue
                if level_filter_set is not None and coerced not in level_filter_set:
                    continue
                if coerced <= 0 or coerced in seen_levels:
                    continue
                seen_levels.add(coerced)
                level_plan.append(coerced)

            if not level_plan:
                logging.info(
                    "Nessun livello selezionato per %s, salto la richiesta",
                    build_request.output_name(),
                )
                continue

            base_level = level_plan[0] if level_plan else 1

            async def process_class(
                request: BuildRequest, destination: Path
            ) -> tuple[str, Mapping]:
                async with semaphore:
                    method = request.http_method()
                    logging.info(
                        "Recupero build per %s (mode=%s, race=%s, archetype=%s, level=%s) via %s",
                        request.class_name,
                        request.mode,
                        request.race,
                        request.archetype,
                        request.level or base_level,
                        method,
                    )
                    try:
                        payload: MutableMapping | None = None
                        for attempt in range(max_retries + 1):
                            try:
                                payload = await fetch_build(
                                    client,
                                    api_key,
                                    request,
                                    max_retries,
                                    require_complete=require_complete,
                                    target_level=request.level,
                                    ruling_expert_url=ruling_expert_url,
                                    ruling_timeout=ruling_timeout,
                                    ruling_max_retries=ruling_max_retries,
                                )
                                break
                            except BuildFetchError as exc:
                                if attempt >= max_retries:
                                    raise
                                delay = 1 + attempt
                                logging.warning(
                                    "Payload incompleto per %s (%s). Retry in %ss...",
                                    request.class_name,
                                    exc,
                                    delay,
                                )
                                await asyncio.sleep(delay)

                        if payload is None:
                            raise BuildFetchError(
                                f"Impossibile recuperare payload per {request.class_name}"
                            )
                        _apply_level_checkpoint(payload, request.level)
                        validation_error = validate_with_schema(
                            schema_for_mode(request.mode),
                            payload,
                            f"build {request.output_name()}",
                            strict=strict,
                        )
                        sheet_context = payload.get("export", {}).get(
                            "sheet_payload"
                        ) or payload.get("sheet_payload")
                        sheet_validation = None
                        if sheet_context is not None:
                            sheet_validation = validate_with_schema(
                                "scheda_pg.schema.json",
                                sheet_context,
                                f"sheet payload {request.output_name()}",
                                strict=strict,
                            )
                        if validation_error and sheet_validation:
                            validation_error = f"{validation_error}; {sheet_validation}"
                        elif validation_error is None:
                            validation_error = sheet_validation
                        completeness_ctx = (
                            payload.get("completeness")
                            if isinstance(payload.get("completeness"), Mapping)
                            else {}
                        )
                        completeness_errors = list(completeness_ctx.get("errors") or [])
                        completeness_text: str | None = None
                        if completeness_errors:
                            completeness_text = "; ".join(
                                str(error) for error in completeness_errors
                            )
                            validation_error = (
                                completeness_text
                                if validation_error is None
                                else f"{validation_error}; {completeness_text}"
                            )
                        incomplete_payload = bool(completeness_errors)
                        status = "ok" if validation_error is None else "invalid"
                        ruling_badge = (
                            payload.get("ruling_badge")
                            if isinstance(payload, Mapping)
                            else None
                        )
                        ruling_sources = (
                            payload.get("ruling_sources")
                            if isinstance(payload, Mapping)
                            else None
                        )
                        if incomplete_payload:
                            status = "invalid"
                            logging.warning(
                                "Payload per %s scartato per incompletezza: %s",
                                request.output_name(),
                                completeness_text or "dati mancanti",
                            )
                            if destination.exists():
                                destination.unlink()
                            output_path: Path | None = None
                        elif status == "ok" or keep_invalid:
                            if skip_unchanged and destination.exists():
                                try:
                                    existing_payload = json.loads(
                                        destination.read_text(encoding="utf-8")
                                    )
                                except Exception:
                                    existing_payload = None

                                comparison_payload: object = payload
                                if isinstance(payload, Mapping):
                                    comparison_payload = dict(payload)
                                    if isinstance(existing_payload, Mapping):
                                        comparison_payload["fetched_at"] = (
                                            existing_payload.get("fetched_at")
                                        )

                                if existing_payload == comparison_payload:
                                    logging.info(
                                        "Payload invariato per %s, salto la scrittura",
                                        request.output_name(),
                                    )
                                    output_path = destination
                                    return destination.name, build_index_entry(
                                        request,
                                        output_path,
                                        status,
                                        validation_error,
                                        payload.get("step_audit"),
                                        completeness_errors,
                                        ruling_badge,
                                        ruling_sources,
                                    )

                            destination.write_text(
                                json.dumps(payload, indent=2, ensure_ascii=False),
                                encoding="utf-8",
                            )
                            output_path = destination
                        else:
                            if destination.exists():
                                destination.unlink()
                            logging.warning(
                                "Payload per %s scartato per invalidazione: %s",
                                request.output_name(),
                                validation_error,
                            )
                            output_path = None
                        return destination.name, build_index_entry(
                            request,
                            output_path,
                            status,
                            validation_error,
                            payload.get("step_audit"),
                            completeness_errors,
                            ruling_badge,
                            ruling_sources,
                        )
                    except ValidationError:
                        raise
                    except BuildFetchError as exc:
                        completeness_errors = getattr(exc, "completeness_errors", None)
                        logging.error(
                            "Build %s marcata come %s: %s",
                            request.class_name,
                            "incompleta" if completeness_errors else "errore",
                            exc,
                        )
                        if destination.exists():
                            destination.unlink()
                        status = "invalid" if completeness_errors else "error"
                        return destination.name, build_index_entry(
                            request,
                            None,
                            status,
                            str(exc),
                            (
                                payload.get("step_audit")
                                if isinstance(payload, Mapping)
                                else None
                            ),
                            completeness_errors,
                            (
                                payload.get("ruling_badge")
                                if isinstance(payload, Mapping)
                                else None
                            ),
                            (
                                payload.get("ruling_sources")
                                if isinstance(payload, Mapping)
                                else None
                            ),
                        )
                    except Exception as exc:  # pragma: no cover - network dependent
                        logging.exception(
                            "Errore durante la fetch di %s", request.class_name
                        )
                        return destination.name, build_index_entry(
                            request,
                            None,
                            "error",
                            str(exc),
                            (
                                payload.get("step_audit")
                                if isinstance(payload, Mapping)
                                else None
                            ),
                            (
                                (
                                    completeness_errors
                                    if "completeness_errors" in locals()
                                    else None
                                ),
                            ),
                            (
                                payload.get("ruling_badge")
                                if isinstance(payload, Mapping)
                                else None
                            ),
                            (
                                payload.get("ruling_sources")
                                if isinstance(payload, Mapping)
                                else None
                            ),
                        )

            for idx, level in enumerate(level_plan):
                if max_items is not None and snapshots_planned >= max_items:
                    skipped_for_limit += len(level_plan) - idx
                    limit_reached = True
                    break
                task_request = replace(
                    build_request,
                    level=level,
                    level_checkpoints=tuple(level_plan),
                )
                suffix = "" if level == base_level else f"_lvl{level:02d}"
                output_file = output_dir / f"{task_request.output_name()}{suffix}.json"

                build_tasks.append(
                    asyncio.create_task(process_class(task_request, output_file))
                )
                snapshots_planned += 1

        if skipped_for_limit:
            logging.info(
                "Limite max-items=%s raggiunto: scartati %s snapshot aggiuntivi",
                max_items,
                skipped_for_limit,
            )

        module_tasks = []
        for module_name in module_plan:
            module_path = modules_output_dir / module_name

            async def process_module(
                name: str, destination: Path
            ) -> tuple[str, Mapping]:
                async with semaphore:
                    logging.info("Scarico modulo raw %s", name)
                    try:
                        content, meta = await fetch_module(
                            client, api_key, name, max_retries
                        )
                        validation_error = validate_with_schema(
                            MODULE_SCHEMA,
                            meta,
                            f"module meta {name}",
                            strict=strict,
                        )
                        status = "ok" if validation_error is None else "invalid"
                        destination_path: Path | None = None
                        if status == "ok" or keep_invalid:
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            destination.write_text(content, encoding="utf-8")
                            destination_path = destination
                        elif destination.exists():
                            destination.unlink()
                        return name, module_index_entry(
                            name,
                            destination_path,
                            status,
                            meta if validation_error is None else None,
                            validation_error,
                        )
                    except ValidationError:
                        raise
                    except Exception as exc:  # pragma: no cover - network dependent
                        logging.exception("Errore durante il download di %s", name)
                        return name, module_index_entry(
                            name, None, "error", error=str(exc)
                        )

            module_tasks.append(
                asyncio.create_task(process_module(module_name, module_path))
            )

        build_results = await asyncio.gather(*build_tasks)
        module_results = await asyncio.gather(*module_tasks)

    builds_index["entries"].extend(
        entry for _, entry in sorted(build_results, key=lambda item: item[0])
    )
    builds_index["checkpoints"] = _checkpoint_summary_from_entries(
        builds_index["entries"]
    )
    new_module_entries = {name: entry for name, entry in module_results}
    merged_module_entries = []
    for name in sorted(set(new_module_entries) | set(existing_module_entries)):
        if name in new_module_entries:
            merged_module_entries.append(new_module_entries[name])
        else:
            merged_module_entries.append(existing_module_entries[name])

    modules_index["entries"] = merged_module_entries
    if discovery_info:
        modules_index["discovery"] = discovery_info

    write_json(index_path, builds_index)
    write_json(module_index_path, modules_index)
    logging.info("Indici aggiornati: %s e %s", index_path, module_index_path)


def run_dual_pass_harvest(args: argparse.Namespace) -> Mapping[str, Any]:
    requests = filter_requests(
        build_requests_from_args(args),
        args.filter_classes,
        args.filter_levels,
    )
    requests, window = select_request_window(
        requests,
        offset=args.offset,
        max_items=args.max_items,
        page=args.page,
        page_size=args.page_size,
    )
    log_request_batch(requests, window)
    strict_output_dir = args.output_dir / "strict"
    strict_modules_dir = args.modules_output_dir / "strict"
    strict_build_index = path_with_suffix(args.index_path, "strict")
    strict_module_index = path_with_suffix(args.module_index_path, "strict")

    report: dict[str, Any] = {
        "strict": {
            "output_dir": str(strict_output_dir),
            "modules_output_dir": str(strict_modules_dir),
            "build_index": str(strict_build_index),
            "module_index": str(strict_module_index),
        },
        "tolerant": {
            "output_dir": str(args.output_dir),
            "modules_output_dir": str(args.modules_output_dir),
            "build_index": str(args.index_path),
            "module_index": str(args.module_index_path),
            "keep_invalid": True,
        },
    }

    try:
        asyncio.run(
            run_harvest(
                requests,
                args.api_url,
                args.api_key,
                strict_output_dir,
                strict_build_index,
                args.modules,
                strict_modules_dir,
                strict_module_index,
                args.concurrency,
                args.max_retries,
                args.spec_file,
                args.discover_modules,
                args.include,
                args.exclude,
                strict=True,
                keep_invalid=False,
                require_complete=args.require_complete,
                skip_health_check=args.skip_health_check,
                level_filters=args.filter_levels,
                skip_unchanged=args.skip_unchanged,
                max_items=args.max_items,
                ruling_expert_url=args.ruling_expert_url,
                ruling_timeout=args.ruling_timeout,
                ruling_max_retries=args.ruling_max_retries,
            )
        )
        report["strict"]["status"] = "ok"
    except Exception as exc:
        logging.warning(
            "Passaggio strict fallito, procedo con il run tollerante: %s", exc
        )
        report["strict"].update({"status": "failed", "error": str(exc)})

    try:
        asyncio.run(
            run_harvest(
                requests,
                args.api_url,
                args.api_key,
                args.output_dir,
                args.index_path,
                args.modules,
                args.modules_output_dir,
                args.module_index_path,
                args.concurrency,
                args.max_retries,
                args.spec_file,
                args.discover_modules,
                args.include,
                args.exclude,
                strict=False,
                keep_invalid=True,
                require_complete=args.require_complete,
                skip_health_check=args.skip_health_check,
                level_filters=args.filter_levels,
                skip_unchanged=args.skip_unchanged,
                max_items=args.max_items,
                ruling_expert_url=args.ruling_expert_url,
                ruling_timeout=args.ruling_timeout,
                ruling_max_retries=args.ruling_max_retries,
            )
        )
        report["tolerant"]["status"] = "ok"
        if args.invalid_archive_dir:
            analysis = analyze_indices(
                args.index_path,
                args.module_index_path,
                archive_dir=args.invalid_archive_dir,
            )
        else:
            analysis = analyze_indices(args.index_path, args.module_index_path)
        report["analysis"] = analysis
    except Exception as exc:
        logging.error("Passaggio tollerante fallito: %s", exc)
        report["tolerant"].update({"status": "failed", "error": str(exc)})

    if args.dual_pass_report:
        write_json(args.dual_pass_report, report)
        logging.info("Report dual-pass salvato in %s", args.dual_pass_report)

    return report


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    if args.dual_pass and args.validate_db:
        raise ValueError("--dual-pass non è compatibile con --validate-db")

    if not args.ruling_expert_url and not args.validate_db:
        raise ValueError("--ruling-expert-url è obbligatorio per salvare nuovi snapshot")

    if args.dual_pass:
        run_dual_pass_harvest(args)
        return

    requests = filter_requests(
        build_requests_from_args(args),
        args.filter_classes,
        args.filter_levels,
    )
    requests, window = select_request_window(
        requests,
        offset=args.offset,
        max_items=args.max_items,
        page=args.page,
        page_size=args.page_size,
    )
    log_request_batch(requests, window)
    strict_mode = args.strict and not args.warn_only

    if args.validate_db:
        review_local_database(
            args.output_dir,
            args.modules_output_dir,
            build_index_path=args.index_path,
            module_index_path=args.module_index_path,
            strict=strict_mode,
            output_path=args.review_output,
        )
        return

    asyncio.run(
        run_harvest(
            requests,
            args.api_url,
            args.api_key,
            args.output_dir,
            args.index_path,
            args.modules,
            args.modules_output_dir,
            args.module_index_path,
            args.concurrency,
            args.max_retries,
            args.spec_file,
            args.discover_modules,
            args.include,
            args.exclude,
            strict_mode,
            args.keep_invalid,
            args.require_complete,
            args.skip_health_check,
            args.filter_levels,
            args.skip_unchanged,
            args.max_items,
            args.ruling_expert_url,
            args.ruling_timeout,
            args.ruling_max_retries,
        )
    )


if __name__ == "__main__":
    main()
