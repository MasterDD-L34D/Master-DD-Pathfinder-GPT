"""Utility per popolare il database locale di build MinMax Builder."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence

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


class BuildFetchError(Exception):
    """Raised when the build API does not return usable data."""


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def ensure_output_dirs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


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
        "--modules",
        nargs="*",
        default=list(DEFAULT_MODULE_TARGETS),
        help="Elenco moduli da scaricare in parallelo alle build",
    )
    parser.add_argument(
        "classes",
        nargs="*",
        default=PF1E_CLASSES,
        help="Sovrascrive la lista di classi PF1e da generare",
    )
    return parser.parse_args()


def fetch_build(
    client: httpx.Client, base_url: str, api_key: str | None, class_name: str, mode: str
) -> MutableMapping:
    params = {"mode": mode, "class": class_name}
    headers = {"x-api-key": api_key} if api_key else {}
    url = base_url.rstrip("/") + MODULE_ENDPOINT
    response = client.get(url, params=params, headers=headers, timeout=60)
    response.raise_for_status()

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:  # pragma: no cover - network dependent
        raise BuildFetchError(f"Risposta non JSON per {class_name}: {exc}") from exc

    for required in ("build_state", "benchmark", "export"):
        if required not in payload:
            raise BuildFetchError(
                f"Campo '{required}' mancante nella risposta per {class_name}. Chiavi viste: {sorted(payload.keys())}"
            )

    payload.update({
        "class": class_name,
        "mode": mode,
        "source_url": str(response.url),
        "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    })
    return payload


def fetch_module(client: httpx.Client, base_url: str, api_key: str | None, module_name: str) -> tuple[str, Mapping]:
    headers = {"x-api-key": api_key} if api_key else {}
    base = base_url.rstrip("/")
    content_resp = client.get(
        MODULE_DUMP_ENDPOINT.format(name=module_name),
        headers=headers,
        base_url=base,
        timeout=60,
    )
    content_resp.raise_for_status()

    meta_resp = client.get(
        MODULE_META_ENDPOINT.format(name=module_name),
        headers=headers,
        base_url=base,
        timeout=30,
    )
    meta_resp.raise_for_status()

    return content_resp.text, meta_resp.json()


def write_json(path: Path, data: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_index_entry(class_name: str, output_file: Path, status: str, error: str | None = None) -> Mapping:
    entry: dict[str, object] = {
        "class": class_name,
        "file": str(output_file) if output_file else None,
        "status": status,
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


def run_harvest(
    classes: Iterable[str],
    api_url: str,
    api_key: str | None,
    mode: str,
    output_dir: Path,
    index_path: Path,
    modules: Sequence[str],
    modules_output_dir: Path,
    module_index_path: Path,
) -> None:
    ensure_output_dirs(output_dir)
    ensure_output_dirs(modules_output_dir)
    builds_index: dict[str, object] = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "api_url": api_url,
        "mode": mode,
        "entries": [],
    }
    modules_index: dict[str, object] = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "api_url": api_url,
        "entries": [],
    }

    with httpx.Client(follow_redirects=True) as client:
        for class_name in classes:
            slug = slugify(class_name)
            output_file = output_dir / f"{slug}.json"
            logging.info("Recupero build per %s in modalità %s", class_name, mode)
            try:
                payload = fetch_build(client, api_url, api_key, class_name, mode)
                write_json(output_file, payload)
                builds_index["entries"].append(build_index_entry(class_name, output_file, "ok"))
            except Exception as exc:  # pragma: no cover - network dependent
                logging.exception("Errore durante la fetch di %s", class_name)
                builds_index["entries"].append(build_index_entry(class_name, None, "error", str(exc)))

        for module_name in modules:
            module_path = modules_output_dir / module_name
            logging.info("Scarico modulo raw %s", module_name)
            try:
                content, meta = fetch_module(client, api_url, api_key, module_name)
                module_path.parent.mkdir(parents=True, exist_ok=True)
                module_path.write_text(content, encoding="utf-8")
                modules_index["entries"].append(module_index_entry(module_name, module_path, "ok", meta))
            except Exception as exc:  # pragma: no cover - network dependent
                logging.exception("Errore durante il download di %s", module_name)
                modules_index["entries"].append(module_index_entry(module_name, None, "error", error=str(exc)))

    write_json(index_path, builds_index)
    write_json(module_index_path, modules_index)
    logging.info("Indici aggiornati: %s e %s", index_path, module_index_path)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    run_harvest(
        args.classes,
        args.api_url,
        args.api_key,
        args.mode,
        args.output_dir,
        args.index_path,
        args.modules,
        args.modules_output_dir,
        args.module_index_path,
    )


if __name__ == "__main__":
    main()
