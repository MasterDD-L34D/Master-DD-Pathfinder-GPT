"""Utility per popolare il database locale di build MinMax Builder."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from fnmatch import fnmatchcase
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence

import yaml

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


@dataclass(slots=True)
class BuildRequest:
    class_name: str
    mode: str = DEFAULT_MODE
    filename_prefix: str | None = None
    spec_id: str | None = None
    race: str | None = None
    archetype: str | None = None
    model: str | None = None
    background: str | None = None
    query_params: Mapping[str, object] = field(default_factory=dict)
    body_params: Mapping[str, object] = field(default_factory=dict)

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

        return {
            "class": self.class_name,
            "race": resolved_race,
            "archetype": resolved_archetype,
            "mode": self.mode,
            "mode_normalized": normalize_mode(self.mode),
            "spec_id": self.spec_id,
            "model": self.model,
            "background": resolved_background,
        }


class BuildFetchError(Exception):
    """Raised when the build API does not return usable data."""


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
    resolver = RefResolver(base_uri=path.resolve().as_uri(), referrer=schema, store=_schema_store)
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
    log_fn("Payload %s non valido (%s): %s", context, schema_filename, message)
    if strict:
        raise ValidationError(message)
    return message


def apply_glob_filters(entries: Sequence[str], include: Sequence[str], exclude: Sequence[str]) -> list[str]:
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
        entries = raw_data.get("requests")
    else:
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
            body_params=_normalize_mapping(entry.get("body") or entry.get("body_params") or entry.get("json")),
        )

        requests.append(request)

    return requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera un database JSON di build per classe.")
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
        "classes",
        nargs="*",
        default=PF1E_CLASSES,
        help="Sovrascrive la lista di classi PF1e da generare",
    )
    return parser.parse_args()


def build_requests_from_args(args: argparse.Namespace) -> list[BuildRequest]:
    if args.spec_file:
        return load_spec_requests(args.spec_file, args.mode)

    return [BuildRequest(class_name=class_name, mode=args.mode) for class_name in args.classes]


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
                method, url, headers=headers, params=params, json=json_body, timeout=timeout
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
            "Tentativo fallito per %s %s (status %s). Retry in %.1fs...", method, url, response.status_code, delay
        )
        await asyncio.sleep(delay)


async def fetch_build(
    client: httpx.AsyncClient,
    api_key: str | None,
    request: BuildRequest,
    max_retries: int,
) -> MutableMapping:
    params: MutableMapping[str, object] = {"mode": request.mode, "class": request.class_name}
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
        raise BuildFetchError(f"Risposta non JSON per {request.class_name}: {exc}") from exc

    for required in ("build_state", "benchmark", "export"):
        if required not in payload:
            raise BuildFetchError(
                f"Campo '{required}' mancante nella risposta per {request.class_name}. Chiavi viste: {sorted(payload.keys())}"
            )

    sheet = None
    for candidate in ("sheet", "sheet_markup", "sheet_markdown", "sheet_markdown_template"):
        if candidate in payload:
            sheet = payload[candidate]
            break

    narrative = payload.get("narrative")
    ledger = payload.get("ledger") or payload.get("adventurer_ledger")

    build_state = payload.get("build_state") or {}
    normalized_mode = normalize_mode(request.mode)
    expected_step_total = expected_step_total_for_mode(normalized_mode)
    observed_step_total = build_state.get("step_total")
    step_labels = build_state.get("step_labels") if isinstance(build_state, Mapping) else None
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
        "build": {"build_state": payload.get("build_state"), "benchmark": payload.get("benchmark"), "export": payload.get("export")},
    }
    if narrative is not None:
        composite["narrative"] = narrative
    if sheet is not None:
        composite["sheet"] = sheet
    if ledger is not None:
        composite["ledger"] = ledger

    payload.update({
        "class": request.class_name,
        "mode": request.mode,
        "source_url": str(response.url),
        "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
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
    })
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


def build_index_entry(
    request: BuildRequest,
    output_file: Path | None,
    status: str,
    error: str | None = None,
    step_audit: Mapping[str, object] | None = None,
) -> Mapping:
    entry: dict[str, object] = {
        "file": str(output_file) if output_file else None,
        "status": status,
        "output_prefix": request.output_name(),
        **request.metadata(),
    }
    if error:
        entry["error"] = error
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
) -> None:
    requests = list(requests)
    ensure_output_dirs(output_dir)
    ensure_output_dirs(modules_output_dir)
    builds_index: dict[str, object] = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "api_url": api_url,
        "mode": requests[0].mode if requests and len({req.mode for req in requests}) == 1 else "mixed",
        "spec_file": str(spec_path) if spec_path else None,
        "entries": [],
    }
    modules_index: dict[str, object] = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
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
            logging.warning("Impossibile caricare module_index esistente %s: %s", module_index_path, exc)

    include_filters = include_filters or []
    exclude_filters = exclude_filters or []
    discovery_info: Mapping[str, object] | None = None

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async with httpx.AsyncClient(base_url=api_url.rstrip("/"), follow_redirects=True) as client:
        if discover:
            discovered = await discover_modules(client, api_key, max_retries)
            filtered_discovered = apply_glob_filters(discovered, include_filters, exclude_filters)
            discovery_info = {
                "performed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "include_filters": list(include_filters),
                "exclude_filters": list(exclude_filters),
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

        build_tasks = []
        for build_request in requests:
            output_file = output_dir / f"{build_request.output_name()}.json"

            async def process_class(request: BuildRequest, destination: Path) -> tuple[str, Mapping]:
                async with semaphore:
                    method = request.http_method()
                    logging.info(
                        "Recupero build per %s (mode=%s, race=%s, archetype=%s) via %s",
                        request.class_name,
                        request.mode,
                        request.race,
                        request.archetype,
                        method,
                    )
                    try:
                        payload = await fetch_build(client, api_key, request, max_retries)
                        validation_error = validate_with_schema(
                            schema_for_mode(request.mode),
                            payload,
                            f"build {request.output_name()}",
                            strict=strict,
                        )
                        sheet_context = (
                            payload.get("export", {}).get("sheet_payload")
                            or payload.get("sheet_payload")
                        )
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
                        status = "ok" if validation_error is None else "invalid"
                        if status == "ok" or keep_invalid:
                            write_json(destination, payload)
                            output_path: Path | None = destination
                        else:
                            if destination.exists():
                                destination.unlink()
                            output_path = None
                        return request.output_name(), build_index_entry(
                            request,
                            output_path,
                            status,
                            validation_error,
                            payload.get("step_audit"),
                        )
                    except ValidationError:
                        raise
                    except Exception as exc:  # pragma: no cover - network dependent
                        logging.exception("Errore durante la fetch di %s", request.class_name)
                        return request.output_name(), build_index_entry(
                            request,
                            None,
                            "error",
                            str(exc),
                            payload.get("step_audit") if "payload" in locals() else None,
                        )

            build_tasks.append(asyncio.create_task(process_class(build_request, output_file)))

        module_tasks = []
        for module_name in module_plan:
            module_path = modules_output_dir / module_name

            async def process_module(name: str, destination: Path) -> tuple[str, Mapping]:
                async with semaphore:
                    logging.info("Scarico modulo raw %s", name)
                    try:
                        content, meta = await fetch_module(client, api_key, name, max_retries)
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
                        return name, module_index_entry(name, None, "error", error=str(exc))

            module_tasks.append(asyncio.create_task(process_module(module_name, module_path)))

        build_results = await asyncio.gather(*build_tasks)
        module_results = await asyncio.gather(*module_tasks)

    builds_index["entries"].extend(entry for _, entry in sorted(build_results, key=lambda item: item[0]))
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


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    requests = build_requests_from_args(args)
    strict_mode = args.strict and not args.warn_only
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
        )
    )


if __name__ == "__main__":
    main()
