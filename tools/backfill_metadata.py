"""Backfill helper per build e moduli.

Lo script normalizza i payload delle build aggiungendo checkpoint,
feat_plan e citation quando mancanti e riallinea i metadati dei moduli
con hash, tag e reference_urls derivati dal contenuto.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence


def _json_load(path: Path) -> MutableMapping:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _json_dump(path: Path, payload: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _slug_parts(value: str | None) -> list[str]:
    if not value:
        return []
    return [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]


def _iter_strings(node: object) -> Iterable[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, Sequence) and not isinstance(node, (str, bytes)):
        for item in node:
            yield from _iter_strings(item)
    elif isinstance(node, Mapping):
        for value in node.values():
            yield from _iter_strings(value)


def _extract_feat_plan(payload: Mapping) -> list[str]:
    feat_candidates: list[str] = []

    def visit(node: object, key_hint: str | None = None) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                lowered = str(key).lower()
                hint = key_hint or lowered
                if any(token in lowered for token in ("feat", "talent", "talenti")):
                    for candidate in _iter_strings(value):
                        cleaned = str(candidate).strip()
                        if cleaned:
                            feat_candidates.append(cleaned)
                visit(value, hint)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes)):
            for item in node:
                visit(item, key_hint)

    export_ctx = payload.get("export") if isinstance(payload.get("export"), Mapping) else {}
    visit(export_ctx)
    unique_feats = []
    seen: set[str] = set()
    for feat in feat_candidates:
        if feat not in seen:
            seen.add(feat)
            unique_feats.append(feat)
    return unique_feats


URL_REGEX = re.compile(r"https?://\S+")


def _clean_url(url: str) -> str:
    return url.rstrip(". ,;\\\"'(){}[]")


def _extract_citation(payload: Mapping) -> dict:
    sources: set[str] = set()
    reference_urls: set[str] = set()

    def visit(node: object, key_hint: str | None = None) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                lowered = str(key).lower()
                if lowered in {"sources", "fonte", "fonti"} and isinstance(
                    value, Sequence
                ) and not isinstance(value, (str, bytes)):
                    for entry in value:
                        entry_str = str(entry).strip()
                        if entry_str:
                            sources.add(entry_str)
                if isinstance(value, str):
                    for match in URL_REGEX.findall(value):
                        reference_urls.add(_clean_url(match))
                visit(value, lowered)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes)):
            for item in node:
                visit(item, key_hint)
        elif isinstance(node, str):
            for match in URL_REGEX.findall(node):
                reference_urls.add(_clean_url(match))

    visit(payload.get("export") if isinstance(payload.get("export"), Mapping) else {})

    return {
        "sources": sorted(sources),
        "reference_urls": sorted(reference_urls),
    }


def _build_checkpoints(entry: Mapping, payload: Mapping) -> list[dict]:
    if payload.get("checkpoints"):
        return list(payload["checkpoints"])  # type: ignore[arg-type]

    level_checkpoints = entry.get("level_checkpoints") or []
    if not isinstance(level_checkpoints, Sequence):
        level_checkpoints = []
    levels: list[int] = [
        int(level) for level in level_checkpoints if isinstance(level, (int, float))
    ]
    if not levels:
        level = entry.get("level") or payload.get("level")
        if isinstance(level, (int, float)):
            levels = [int(level)]

    benchmark = payload.get("benchmark") if isinstance(payload.get("benchmark"), Mapping) else {}
    ruling_badge = (
        payload.get("ruling_badge")
        or benchmark.get("ruling_badge")
        or entry.get("ruling_badge")
    )
    meta_tier = benchmark.get("meta_tier") if isinstance(benchmark, Mapping) else None
    checkpoints: list[dict] = []
    for level in levels:
        checkpoints.append(
            {
                "level": level,
                "status": entry.get("status") or payload.get("status") or "unknown",
                "bench_log": f"Checkpoint auto-generato livello {level}",
                "ruling_badge": ruling_badge,
                "meta_tier": meta_tier,
            }
        )
    return checkpoints


@dataclass
class Paths:
    source_root: Path
    output_root: Path

    def resolve_out(self, path: Path) -> Path:
        relative = path.relative_to(self.source_root)
        return self.output_root / relative


def backfill_builds(paths: Paths) -> None:
    build_index_path = paths.source_root / "src/data/build_index.json"
    build_index = _json_load(build_index_path)
    entry_by_file = {entry["file"]: entry for entry in build_index.get("entries", [])}

    for file_ref, entry in entry_by_file.items():
        source_path = paths.source_root / file_ref
        if not source_path.exists():
            continue
        payload = _json_load(source_path)

        checkpoints = _build_checkpoints(entry, payload)
        payload["checkpoints"] = checkpoints
        payload["feat_plan"] = _extract_feat_plan(payload)
        payload["citation"] = _extract_citation(payload)

        out_path = paths.resolve_out(source_path)
        _json_dump(out_path, payload)

        entry["checkpoints"] = checkpoints
        entry["feat_plan"] = payload.get("feat_plan")
        entry["citation"] = payload.get("citation")

    build_index["generated_at"] = datetime.now(timezone.utc).isoformat()
    out_index_path = paths.resolve_out(build_index_path)
    _json_dump(out_index_path, build_index)


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _parse_header_tags(content: str) -> list[str]:
    tags: set[str] = set()
    for line in content.splitlines():
        if not line.strip():
            continue
        if line.lower().startswith("type:"):
            _, value = line.split(":", 1)
            for part in value.split("/"):
                part_clean = part.strip()
                if part_clean:
                    tags.add(part_clean)
        if line.lower().startswith("module_name:"):
            _, value = line.split(":", 1)
            tags.update(_slug_parts(value))
        if ":" not in line:
            break
    return sorted(tags)


def _extract_reference_urls(content: str) -> list[str]:
    return sorted({_clean_url(match) for match in URL_REGEX.findall(content)})


def backfill_modules(paths: Paths) -> None:
    module_index_path = paths.source_root / "src/data/module_index.json"
    module_index = _json_load(module_index_path)

    for entry in module_index.get("entries", []):
        file_ref = entry.get("file")
        if not file_ref:
            continue
        source_path = paths.source_root / file_ref
        if not source_path.exists():
            continue
        content = source_path.read_text(encoding="utf-8")

        meta = entry.setdefault("meta", {})
        meta["hash_sha256"] = _hash_file(source_path)
        meta["tags"] = _parse_header_tags(content)
        meta["reference_urls"] = _extract_reference_urls(content)

        out_path = paths.resolve_out(source_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if paths.output_root != paths.source_root:
            out_path.write_text(content, encoding="utf-8")

    module_index["generated_at"] = datetime.now(timezone.utc).isoformat()
    out_index_path = paths.resolve_out(module_index_path)
    _json_dump(out_index_path, module_index)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill build e moduli")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Percorso radice sorgente (repo)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Cartella di output; se omessa scrive in-place",
    )
    args = parser.parse_args()

    source_root: Path = args.source_root
    output_root: Path = args.output_dir or source_root

    paths = Paths(source_root=source_root, output_root=output_root)
    backfill_builds(paths)
    backfill_modules(paths)


if __name__ == "__main__":
    main()
