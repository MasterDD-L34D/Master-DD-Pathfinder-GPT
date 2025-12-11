import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.generate_module_plan import collect_section_lines, summarise_module


def test_collect_section_lines_merges_all_matches():
    sections = [
        ("Fix necessari", ["- primo fix", ""]),
        ("Note e miglioramenti", ["- miglioramento"],),
        ("Fix necessari (API)", ["- secondo fix"]),
    ]

    patterns = [re.compile(r"fix", re.IGNORECASE)]

    merged = collect_section_lines(sections, patterns)

    assert merged == ["- primo fix", "", "- secondo fix"]


def test_summarise_module_merges_duplicate_sections(tmp_path: Path):
    report = tmp_path / "sample_report.md"
    report.write_text(
        "\n".join(
            [
                "## Fix necessari",
                "- [P1] Primo fix",
                "",
                "## Fix necessari (API)",
                "- Secondo fix API",
                "",
                "## Note e miglioramenti",
                "- [P3] Ritocco opzionale",
                "",
                "## Errori",
                "- Errore nelle API",
                "",
                "## Errori replicati",
                "- Errore di copia",
                "",
                "## Osservazioni e note",
                "- Nota combinata uno",
                "",
                "## Note e osservazioni",
                "- Nota combinata due",
                "",
            ]
        ),
        encoding="utf-8",
    )

    summary = summarise_module("Modulo di test", report)

    assert [(priority, text) for priority, text in summary.tasks] == [
        (1, "Primo fix"),
        (1, "Secondo fix API"),
        (3, "Ritocco opzionale"),
    ]
    assert summary.errors == ["Errore nelle API", "Errore di copia"]
    assert summary.observations == ["Nota combinata uno", "Nota combinata due"]
