#!/usr/bin/env python3
"""Normalize module reports with the standard checklist.

The script guarantees that every report in `reports/module_tests/` contains
the mandatory sections (Ambiente, Esiti API, Metadati, Comandi/Flow, QA,
Osservazioni, Errori, Miglioramenti, Fix necessari). Use `--check` to validate
headings/bullets or `--write` to insert missing blocks with placeholders.

The module traversal follows the sequence in `planning/module_review_guide.md`
via `load_sequence_from_guide`, aligning automation with the review order.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.generate_module_plan import ALIASES, load_sequence_from_guide, normalise_name

REPORT_DIR = REPO_ROOT / "reports" / "module_tests"


@dataclass
class SectionSpec:
    label: str
    heading: str
    patterns: Tuple[re.Pattern[str], ...]
    placeholder: str


SECTION_SPECS: Sequence[SectionSpec] = (
    SectionSpec(
        label="Ambiente",
        heading="## Ambiente",
        patterns=(re.compile(r"ambiente", re.IGNORECASE),),
        placeholder="- TODO: descrivi l'ambiente di test, flag e variabili.",
    ),
    SectionSpec(
        label="Esiti API",
        heading="## Esiti API",
        patterns=(re.compile(r"esiti\s*api", re.IGNORECASE),),
        placeholder="- TODO: riassumi gli esiti per health/modules/meta/download/404/troncamento.",
    ),
    SectionSpec(
        label="Metadati",
        heading="## Metadati",
        patterns=(re.compile(r"metadati", re.IGNORECASE),),
        placeholder="- TODO: nome modulo, versione, scopo, trigger/policy rilevanti.",
    ),
    SectionSpec(
        label="Comandi/Flow",
        heading="## Comandi/Flow",
        patterns=(re.compile(r"comandi", re.IGNORECASE), re.compile(r"flow", re.IGNORECASE)),
        placeholder="- TODO: elenca comandi principali, auto-invocazioni, CTA e output attesi.",
    ),
    SectionSpec(
        label="QA",
        heading="## QA",
        patterns=(re.compile(r"\bqa\b", re.IGNORECASE),),
        placeholder="- TODO: template QA, gate PF1e, controlli sicurezza e receipt.",
    ),
    SectionSpec(
        label="Osservazioni",
        heading="## Osservazioni",
        patterns=(re.compile(r"osservaz", re.IGNORECASE),),
        placeholder="- TODO: note osservazioni sintetiche con citazioni.",
    ),
    SectionSpec(
        label="Errori",
        heading="## Errori",
        patterns=(re.compile(r"errori", re.IGNORECASE),),
        placeholder="- TODO: errori riscontrati con priorità e citazioni.",
    ),
    SectionSpec(
        label="Miglioramenti",
        heading="## Miglioramenti",
        patterns=(re.compile(r"migliorament", re.IGNORECASE),),
        placeholder="- TODO: miglioramenti e suggerimenti QA/UX.",
    ),
    SectionSpec(
        label="Fix necessari",
        heading="## Fix necessari",
        patterns=(re.compile(r"fix\s+necessari", re.IGNORECASE),),
        placeholder="- TODO: fix da eseguire con priorità P1/P2/P3 e scope.",
    ),
)


@dataclass
class Section:
    heading: str
    start: int
    end: int
    lines: List[str]


def parse_sections(lines: List[str]) -> List[Section]:
    sections: List[Section] = []
    heading_re = re.compile(r"^##\s+(.*)$")
    current: Optional[Tuple[str, int]] = None

    for idx, raw_line in enumerate(lines):
        match = heading_re.match(raw_line.strip())
        if match:
            if current is not None:
                heading, start_idx = current
                sections.append(
                    Section(heading=heading, start=start_idx, end=idx, lines=lines[start_idx + 1 : idx])
                )
            current = (match.group(1).strip(), idx)
    if current is not None:
        heading, start_idx = current
        sections.append(Section(heading=heading, start=start_idx, end=len(lines), lines=lines[start_idx + 1 :]))

    return sections


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def map_reports() -> Dict[str, Path]:
    mapping: Dict[str, Path] = {}
    for report in REPORT_DIR.glob("*.md"):
        mapping[report.stem.lower()] = report
    return mapping


@dataclass
class ValidationResult:
    module_label: str
    report_path: Optional[Path]
    missing_sections: List[str]
    empty_sections: List[str]

    @property
    def ok(self) -> bool:
        return not self.missing_sections and not self.empty_sections


def find_matching_section(spec: SectionSpec, sections: Sequence[Section]) -> Optional[Section]:
    for section in sections:
        if any(pattern.search(section.heading) for pattern in spec.patterns):
            return section
    return None


def has_bullet(content_lines: Iterable[str]) -> bool:
    return any(line.strip().startswith("- ") for line in content_lines)


def validate_report(module_label: str, report_path: Optional[Path]) -> ValidationResult:
    if not report_path or not report_path.exists():
        return ValidationResult(module_label, report_path, [spec.label for spec in SECTION_SPECS], [])

    lines = report_path.read_text(encoding="utf-8").splitlines()
    sections = parse_sections(lines)

    missing: List[str] = []
    empty: List[str] = []

    for spec in SECTION_SPECS:
        section = find_matching_section(spec, sections)
        if section is None:
            missing.append(spec.label)
            continue
        if not has_bullet(section.lines):
            empty.append(spec.label)

    return ValidationResult(module_label, report_path, missing, empty)


def insert_placeholder(lines: List[str], section: Section, placeholder: str) -> None:
    insertion_index = section.end
    lines.insert(insertion_index, placeholder)
    lines.insert(insertion_index, "")


def add_missing_section(lines: List[str], spec: SectionSpec) -> None:
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(spec.heading)
    lines.append("")
    lines.append(spec.placeholder)
    lines.append("")


def refresh_report(module_label: str, report_path: Path) -> ValidationResult:
    lines: List[str]
    if report_path.exists():
        lines = report_path.read_text(encoding="utf-8").splitlines()
    else:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# Report modulo `{module_label}`", ""]

    modified = False

    for spec in SECTION_SPECS:
        sections = parse_sections(lines)
        section = find_matching_section(spec, sections)
        if section is None:
            add_missing_section(lines, spec)
            modified = True
            continue
        if not has_bullet(section.lines):
            insert_placeholder(lines, section, spec.placeholder)
            modified = True

    if modified:
        report_path.write_text(ensure_trailing_newline("\n".join(lines)), encoding="utf-8")

    # Re-parse to reflect any additions for validation output
    final_validation = validate_report(module_label, report_path)
    return final_validation


def resolve_report_path(module_label: str, existing: Dict[str, Path]) -> Path:
    stem = normalise_name(module_label)
    stem = ALIASES.get(stem, stem)
    filename = f"{stem}.md"
    return existing.get(stem, REPORT_DIR / filename)


def run(mode: str) -> int:
    sequence = load_sequence_from_guide()
    report_map = map_reports()

    results: List[ValidationResult] = []
    for module in sequence:
        report_path = resolve_report_path(module, report_map)
        if mode == "check":
            results.append(validate_report(module, report_path if report_path.exists() else None))
        else:
            results.append(refresh_report(module, report_path))

    failures = [res for res in results if not res.ok]

    for res in failures:
        path_label = "mancante" if not res.report_path else res.report_path.relative_to(REPO_ROOT)
        if res.missing_sections:
            print(f"[{res.module_label}] sezioni mancanti ({path_label}): {', '.join(res.missing_sections)}")
        if res.empty_sections:
            print(f"[{res.module_label}] sezioni senza bullet ({path_label}): {', '.join(res.empty_sections)}")

    if mode == "check" and failures:
        return 1

    print(f"Processed {len(results)} report(s) with mode={mode}.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifica o aggiorna i report dei moduli.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Solo verifica: exit 1 se mancano sezioni richieste.")
    group.add_argument("--write", action="store_true", help="Aggiorna i report aggiungendo sezioni mancanti e placeholder.")

    args = parser.parse_args()
    mode = "check" if args.check else "write"
    sys.exit(run(mode))


if __name__ == "__main__":
    main()
