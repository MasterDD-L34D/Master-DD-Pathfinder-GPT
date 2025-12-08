"""Utility per popolare il database locale di build MinMax Builder."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence

import yaml

import httpx

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

    def output_name(self) -> str:
        if self.filename_prefix:
            return self.filename_prefix
        if self.spec_id:
            return slugify(self.spec_id)
        return slugify(self.class_name)

    def metadata(self) -> Mapping[str, object | None]:
        return {
            "class": self.class_name,
            "race": self.race,
            "archetype": self.archetype,
            "mode": self.mode,
            "spec_id": self.spec_id,
            "model": self.model,
            "background": self.background,
        }


class BuildFetchError(Exception):
    """Raised when the build API does not return usable data."""


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def ensure_output_dirs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def _normalize_mapping(data: Mapping | None) -> Mapping[str, object]:
    return {str(key): value for key, value in (data or {}).items() if value is not None}


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
        choices=["core", "extended"],
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
        response = await client.request(
            method, url, headers=headers, params=params, json=json_body, timeout=timeout
        )
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
    response = await request_with_retry(
        client,
        "GET",
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


def write_json(path: Path, data: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_index_entry(request: BuildRequest, output_file: Path, status: str, error: str | None = None) -> Mapping:
    entry: dict[str, object] = {
        "file": str(output_file) if output_file else None,
        "status": status,
        "output_prefix": request.output_name(),
        **request.metadata(),
    }
    if error:
        entry["error"] = error
    return entry


def module_index_entry(name: str, output_file: Path, status: str, meta: Mapping | None = None, error: str | None = None) -> Mapping:
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

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async with httpx.AsyncClient(base_url=api_url.rstrip("/"), follow_redirects=True) as client:
        build_tasks = []
        for build_request in requests:
            output_file = output_dir / f"{build_request.output_name()}.json"

            async def process_class(request: BuildRequest, destination: Path) -> tuple[str, Mapping]:
                async with semaphore:
                    logging.info(
                        "Recupero build per %s (mode=%s, race=%s, archetype=%s)",
                        request.class_name,
                        request.mode,
                        request.race,
                        request.archetype,
                    )
                    try:
                        payload = await fetch_build(client, api_key, request, max_retries)
                        write_json(destination, payload)
                        return request.output_name(), build_index_entry(request, destination, "ok")
                    except Exception as exc:  # pragma: no cover - network dependent
                        logging.exception("Errore durante la fetch di %s", request.class_name)
                        return request.output_name(), build_index_entry(request, None, "error", str(exc))

            build_tasks.append(asyncio.create_task(process_class(build_request, output_file)))

        module_tasks = []
        for module_name in modules:
            module_path = modules_output_dir / module_name

            async def process_module(name: str, destination: Path) -> tuple[str, Mapping]:
                async with semaphore:
                    logging.info("Scarico modulo raw %s", name)
                    try:
                        content, meta = await fetch_module(client, api_key, name, max_retries)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_text(content, encoding="utf-8")
                        return name, module_index_entry(name, destination, "ok", meta)
                    except Exception as exc:  # pragma: no cover - network dependent
                        logging.exception("Errore durante il download di %s", name)
                        return name, module_index_entry(name, None, "error", error=str(exc))

            module_tasks.append(asyncio.create_task(process_module(module_name, module_path)))

        build_results = await asyncio.gather(*build_tasks)
        module_results = await asyncio.gather(*module_tasks)

    builds_index["entries"].extend(entry for _, entry in sorted(build_results, key=lambda item: item[0]))
    modules_index["entries"].extend(entry for _, entry in sorted(module_results, key=lambda item: item[0]))

    write_json(index_path, builds_index)
    write_json(module_index_path, modules_index)
    logging.info("Indici aggiornati: %s e %s", index_path, module_index_path)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    requests = build_requests_from_args(args)
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
        )
    )


if __name__ == "__main__":
    main()
