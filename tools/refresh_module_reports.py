#!/usr/bin/env python3
"""Bootstrap and validate standard sections in module test reports.

The enforced sections mirror the review checklist:
Ambiente, Esiti API, Metadati, Comandi/Flow, QA, Osservazioni,
Errori, Miglioramenti, Fix necessari. Missing sections are added
with bullet placeholders so every report is ready for manual
compilazione.

The script reuses the utilities from :mod:`tools.generate_module_plan` to keep
coverage aligned with the planning guide:

- :func:`load_sequence_from_guide` to read the canonical module order from
  ``planning/module_review_guide.md``.
- :func:`map_reports` to resolve all reports under ``reports/module_tests/``.

With ``--check`` it fails when a report lacks mandatory sections; with
``--write`` it appends missing headings (and basic placeholders for metadata
and comandi) to every report in the sequence.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.generate_module_plan import find_report, load_sequence_from_guide, map_reports

REPORT_DIR = REPO_ROOT / "reports" / "module_tests"
MODULE_DIR = REPO_ROOT / "src" / "modules"


@dataclass(frozen=True)
class SectionSpec:
    name: str
    heading: str
    patterns: Sequence[re.Pattern[str]]


@dataclass(frozen=True)
class ModuleInfo:
    module_name: Optional[str]
    version: Optional[str]
    triggers: List[str]
    commands: List[str]
    source_path: Path


SECTION_SPECS: Sequence[SectionSpec] = (
    SectionSpec(
        name="ambiente",
        heading="Ambiente di test",
        patterns=(re.compile(r"ambiente", re.IGNORECASE),),
    ),
    SectionSpec(
        name="esiti",
        heading="Esiti API",
        patterns=(re.compile(r"esiti\s+api", re.IGNORECASE),),
    ),
    SectionSpec(
        name="metadati",
        heading="Metadati",
        patterns=(re.compile(r"metadati", re.IGNORECASE),),
    ),
    SectionSpec(
        name="comandi",
        heading="Comandi e flow",
        patterns=(
            re.compile(r"comandi", re.IGNORECASE),
            re.compile(r"flow", re.IGNORECASE),
        ),
    ),
    SectionSpec(
        name="qa",
        heading="QA",
        patterns=(
            re.compile(r"qa\s+templates?", re.IGNORECASE),
            re.compile(r"qa", re.IGNORECASE),
            re.compile(r"helper", re.IGNORECASE),
        ),
    ),
    SectionSpec(
        name="osservazioni",
        heading="Osservazioni",
        patterns=(re.compile(r"osservazion", re.IGNORECASE),),
    ),
    SectionSpec(
        name="errori",
        heading="Errori",
        patterns=(re.compile(r"errori", re.IGNORECASE),),
    ),
    SectionSpec(
        name="miglioramenti",
        heading="Miglioramenti",
        patterns=(re.compile(r"miglioramenti", re.IGNORECASE),),
    ),
    SectionSpec(
        name="fix",
        heading="Fix necessari",
        patterns=(re.compile(r"fix\s+necessari", re.IGNORECASE),),
    ),
)


def find_missing_sections(lines: List[str]) -> tuple[List[SectionSpec], List[SectionSpec]]:
    missing_headings: List[SectionSpec] = []
    empty_sections: List[SectionSpec] = []
    for spec in SECTION_SPECS:
        section_range = find_section_range(lines, spec)
        if not section_range:
            missing_headings.append(spec)
            continue
        if not section_has_content(lines, section_range):
            empty_sections.append(spec)
    return missing_headings, empty_sections


def extract_triggers(text: str) -> List[str]:
    trigger_lines: List[str] = []
    lines = text.splitlines()
    trigger_header = re.compile(r"^triggers\s*:\s*$", re.IGNORECASE)
    bullet_re = re.compile(r"^\s*-\s*(.+)$")
    collecting = False

    for line in lines:
        if collecting:
            bullet_match = bullet_re.match(line)
            if bullet_match:
                trigger_lines.append(bullet_match.group(1).strip())
                continue
            if not line.startswith(" ") and not line.startswith("\t"):
                break
            if line.strip():
                continue
            break
        elif trigger_header.match(line):
            collecting = True
    return trigger_lines


def extract_commands(text: str) -> List[str]:
    pattern = re.compile(r"/[A-Za-z0-9_]+")
    seen = set()
    commands: List[str] = []
    for match in pattern.finditer(text):
        cmd = match.group(0)
        if cmd not in seen:
            seen.add(cmd)
            commands.append(cmd)
    return commands


def load_module_info(report_path: Path) -> Optional[ModuleInfo]:
    stem = report_path.stem
    module_path = MODULE_DIR / f"{stem}.txt"
    if not module_path.exists():
        print(f"[WARN] Sorgente modulo non trovata: {module_path}")
        return None

    text = module_path.read_text(encoding="utf-8")

    name_match = re.search(r"^(?:module_name|profile_name):\s*(.+)$", text, re.MULTILINE)
    version_match = re.search(r"^version:\s*(.+)$", text, re.MULTILINE)
    triggers = extract_triggers(text)
    commands = extract_commands(text)

    return ModuleInfo(
        module_name=name_match.group(1).strip() if name_match else None,
        version=version_match.group(1).strip() if version_match else None,
        triggers=triggers,
        commands=commands,
        source_path=module_path,
    )


def default_metadati_content(info: Optional[ModuleInfo]) -> List[str]:
    module_name = info.module_name if info and info.module_name else "TODO"
    version = info.version if info and info.version else "TODO"
    triggers = info.triggers if info and info.triggers else []
    trigger_text = ", ".join(triggers) if triggers else "TODO"
    return [
        f"- Nome modulo: **{module_name}**",
        f"- Versione: `{version}`",
        f"- Trigger dichiarati: {trigger_text}",
    ]


def default_commands_content(info: Optional[ModuleInfo]) -> List[str]:
    commands = info.commands if info else []
    command_text = ", ".join(commands) if commands else "TODO"
    return [
        "- Flussi o CTA principali: TODO",
        f"- Comandi rilevati nel modulo: {command_text}",
    ]


SECTION_CONTENT_OVERRIDES: dict[str, Callable[[Optional[ModuleInfo]], List[str]]] = {
    "metadati": default_metadati_content,
    "comandi": default_commands_content,
}


def build_section_content(spec: SectionSpec, info: Optional[ModuleInfo]) -> List[str]:
    if spec.name in SECTION_CONTENT_OVERRIDES:
        return SECTION_CONTENT_OVERRIDES[spec.name](info)
    return ["- TODO"]


def append_sections(path: Path, specs: Sequence[SectionSpec], info: Optional[ModuleInfo]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[-1].strip():
        lines.append("")
    for spec in specs:
        lines.append(f"## {spec.heading}")
        lines.extend(build_section_content(spec, info))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def find_section_range(lines: List[str], spec: SectionSpec) -> Optional[tuple[int, int]]:
    heading_re = re.compile(r"^##\s+(.*)$")
    for index, line in enumerate(lines):
        match = heading_re.match(line.strip())
        if not match:
            continue
        heading = match.group(1).strip()
        if any(pattern.search(heading) for pattern in spec.patterns):
            for end in range(index + 1, len(lines)):
                if heading_re.match(lines[end].strip()):
                    return index, end
            return index, len(lines)
    return None


def section_has_content(lines: List[str], section_range: tuple[int, int]) -> bool:
    start, end = section_range
    return any(line.strip() for line in lines[start + 1 : end])


def populate_section(
    lines: List[str], section_range: tuple[int, int], spec: SectionSpec, info: Optional[ModuleInfo]
) -> List[str]:
    start, end = section_range
    content = build_section_content(spec, info)
    new_lines = lines[: start + 1] + content
    if end < len(lines) and lines[end].strip():
        new_lines.append("")
    new_lines.extend(lines[end:])
    return new_lines


def refresh_report(path: Path, *, write: bool, info: Optional[ModuleInfo]) -> List[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    missing_headings, empty_sections = find_missing_sections(lines)

    if write and missing_headings:
        append_sections(path, missing_headings, info)
        lines = path.read_text(encoding="utf-8").splitlines()

    if write:
        for spec in empty_sections:
            section_range = find_section_range(lines, spec)
            if section_range and not section_has_content(lines, section_range):
                lines = populate_section(lines, section_range, spec, info)
        path.write_text("\n".join(lines), encoding="utf-8")
        lines = path.read_text(encoding="utf-8").splitlines()
        missing_headings, empty_sections = find_missing_sections(lines)

    missing_all = [spec.name for spec in missing_headings + empty_sections]
    return missing_all


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or populate standard sections in module test reports.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Verify reports and exit with status 1 if any section is missing.",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Insert missing sections with empty bullet templates.",
    )

    args = parser.parse_args()

    sequence = load_sequence_from_guide()
    report_map = map_reports()

    missing_overall: dict[str, list[str]] = {}
    processed_stems: set[str] = set()
    for module in sequence:
        report_path = find_report(module, report_map)
        if not report_path:
            missing_overall[module] = ["report"]
            print(f"[SKIP] Report mancante per {module}")
            continue
        module_info = load_module_info(report_path)
        missing = refresh_report(report_path, write=args.write, info=module_info)
        processed_stems.add(report_path.stem.lower())
        if missing:
            missing_overall[module] = missing
            print(f"[MISSING] {module}: {', '.join(missing)}")
        else:
            print(f"[OK] {module}")

    for stem, report_path in sorted(report_map.items()):
        if stem in processed_stems:
            continue
        module_info = load_module_info(report_path)
        missing = refresh_report(report_path, write=args.write, info=module_info)
        label = report_path.stem
        if missing:
            missing_overall[label] = missing
            print(f"[MISSING] {label}: {', '.join(missing)} (fuori sequenza)")
        else:
            print(f"[OK] {label} (fuori sequenza)")

    if args.check:
        if missing_overall:
            print("\nSezioni mancanti trovate:")
            for module, sections in missing_overall.items():
                if sections == ["report"]:
                    print(f"- {module}: report non trovato")
                else:
                    print(f"- {module}: {', '.join(sections)}")
            return 1
        print("Tutte le sezioni standard sono presenti.")
    else:
        print("Aggiornamento completato (le sezioni mancanti hanno un bullet vuoto '- TODO').")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
