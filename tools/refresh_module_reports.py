#!/usr/bin/env python3
"""Ensure module test reports contain standard sections.

The script reads the module sequence from `planning/module_review_guide.md`
(via :func:`load_sequence_from_guide`) and maps report filenames in
`reports/module_tests/` (via :func:`map_reports`). It can either verify the
presence of the standard headings or append missing sections with placeholder
bullets.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from tools.generate_module_plan import find_report, load_sequence_from_guide, map_reports

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "reports" / "module_tests"


@dataclass(frozen=True)
class SectionSpec:
    name: str
    heading: str
    patterns: Sequence[re.Pattern[str]]


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
        patterns=(
            re.compile(r"metadati", re.IGNORECASE),
            re.compile(r"scopo\s+del\s+modulo", re.IGNORECASE),
        ),
    ),
    SectionSpec(
        name="comandi",
        heading="Comandi/Flow",
        patterns=(
            re.compile(r"comandi", re.IGNORECASE),
            re.compile(r"flow", re.IGNORECASE),
        ),
    ),
    SectionSpec(
        name="qa",
        heading="QA",
        patterns=(re.compile(r"qa", re.IGNORECASE),),
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
        heading="Miglioramenti suggeriti",
        patterns=(re.compile(r"miglioramenti", re.IGNORECASE),),
    ),
    SectionSpec(
        name="fix",
        heading="Fix necessari",
        patterns=(re.compile(r"fix\s+necessari", re.IGNORECASE),),
    ),
)


def parse_sections(lines: Iterable[str]) -> List[str]:
    """Return the list of headings (without the leading hashes)."""

    headings: List[str] = []
    pattern = re.compile(r"^##\s+(.*)$")
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            headings.append(match.group(1).strip())
    return headings


def find_missing_sections(existing_headings: Sequence[str]) -> List[SectionSpec]:
    missing: List[SectionSpec] = []
    for spec in SECTION_SPECS:
        if not any(pattern.search(h) for h in existing_headings for pattern in spec.patterns):
            missing.append(spec)
    return missing


def append_sections(path: Path, specs: Sequence[SectionSpec]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[-1].strip():
        lines.append("")
    for spec in specs:
        lines.append(f"## {spec.heading}")
        lines.append("- TODO")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def refresh_report(path: Path, *, write: bool) -> List[str]:
    headings = parse_sections(path.read_text(encoding="utf-8").splitlines())
    missing_specs = find_missing_sections(headings)

    if write and missing_specs:
        append_sections(path, missing_specs)
    return [spec.name for spec in missing_specs]


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
    for module in sequence:
        report_path = find_report(module, report_map)
        if not report_path:
            missing_overall[module] = ["report"]
            print(f"[SKIP] Report mancante per {module}")
            continue
        missing = refresh_report(report_path, write=args.write)
        if missing:
            missing_overall[module] = missing
            print(f"[MISSING] {module}: {', '.join(missing)}")
        else:
            print(f"[OK] {module}")

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
