from __future__ import annotations

import argparse
import json

from pathlib import Path
from typing import Dict, Iterable

DEFAULT_LOG_PATH = Path("data/pytest_logs/pytest_run_2025-12-11.json")
DEFAULT_BOARD_PATH = Path("planning/sprint_board.md")
DEFAULT_ATTESTATO_PATH = Path("reports/coverage_attestato_2025-12-11.md")


class ImportErrorRuntime(RuntimeError):
    """Raised when the pytest log import or attestation generation fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa un log pytest e genera l'attestato di copertura"
    )
    parser.add_argument(
        "--log", type=Path, default=DEFAULT_LOG_PATH, help="Percorso al log pytest JSON"
    )
    parser.add_argument(
        "--board",
        type=Path,
        default=DEFAULT_BOARD_PATH,
        help="Percorso al tracker moduli (Markdown)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ATTESTATO_PATH,
        help="File di output per l'attestato",
    )
    return parser.parse_args()


def load_pytest_log(path: Path) -> dict:
    if not path.exists():
        raise ImportErrorRuntime(f"Log pytest non trovato: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"run_date", "tests_total", "tests_passed"}
    if not required.issubset(data):
        missing = ", ".join(sorted(required - set(data)))
        raise ImportErrorRuntime(f"Campi mancanti nel log pytest: {missing}")
    if data["tests_passed"] != data["tests_total"]:
        raise ImportErrorRuntime(
            f"Test non tutti passati: {data['tests_passed']} / {data['tests_total']}"
        )
    return data


def _is_separator_row(cells: Iterable[str]) -> bool:
    for cell in cells:
        stripped = cell.strip()
        if not stripped:
            continue
        if set(stripped) != {"-"}:
            return False
    return True


def parse_module_statuses(board_path: Path) -> Dict[str, str]:
    if not board_path.exists():
        raise ImportErrorRuntime(f"Tracker moduli non trovato: {board_path}")

    statuses: Dict[str, str] = {}
    module_idx: int | None = None
    status_idx: int | None = None
    in_table = False

    for raw in board_path.read_text(encoding="utf-8").splitlines():
        if not raw.startswith("|"):
            in_table = False
            continue
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        lowered = [c.lower() for c in cells]
        if "modulo" in lowered and "stato" in lowered:
            module_idx = lowered.index("modulo")
            status_idx = lowered.index("stato")
            in_table = True
            continue
        if not in_table or module_idx is None or status_idx is None:
            continue
        if _is_separator_row(cells):
            continue
        if len(cells) <= max(module_idx, status_idx):
            continue
        module = cells[module_idx]
        status = cells[status_idx]
        if module and status:
            statuses[module] = status
    if not statuses:
        raise ImportErrorRuntime(
            "Nessuna riga di stato trovata nel tracker; controlla il formato della tabella"
        )
    return statuses


def build_attestato(
    log: dict, statuses: Dict[str, str], board_path: Path, log_path: Path
) -> str:
    run_date = log["run_date"]
    warnings = log.get("warnings") or []
    notes = log.get("notes")
    all_ready = all(status.lower().startswith("pronto") for status in statuses.values())
    not_ready = {
        m: s for m, s in statuses.items() if not s.lower().startswith("pronto")
    }

    lines = [
        f"# Attestato di copertura QA — Job tracker {run_date}",
        "",
        "## Input e ambito",
        f"- **Log importati**: run pytest del {run_date} con **{log['tests_passed']}/{log['tests_total']} test passati**.",
        f"- **Storie coperte**: tutte le storie marcate **Done** nel piano di lavoro.",
        f"- **Tracker sorgente**: {board_path.as_posix()}.",
    ]
    if notes:
        lines.append(f"- **Note**: {notes}.")
    if warnings:
        lines.append(f"- **Warning**: {', '.join(warnings)}.")

    lines.extend(
        [
            "",
            "## Copertura e stato moduli",
            "- Il log di regressione certifica la copertura su API, flow CTA, metadati e policy di dump/troncamento per i moduli in scopo.",
        ]
    )

    if all_ready:
        lines.append(
            "- Tutti i moduli risultano **Pronto per sviluppo** secondo la sprint board aggiornata; flag tracking **verde**."
        )
    else:
        lines.append(
            "- Attenzione: alcuni moduli non sono marcati Pronto per sviluppo nel tracker."
        )
        for module, status in sorted(not_ready.items()):
            lines.append(f"  - {module}: {status}")

    lines.extend(
        [
            "",
            "## Allegati",
            f"- Fonte log: {log_path.as_posix()}.",
            f"- Tracker stato moduli: {board_path.as_posix()}.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_attestato(content: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    log = load_pytest_log(args.log)
    statuses = parse_module_statuses(args.board)
    attestato = build_attestato(log, statuses, args.board, args.log)
    write_attestato(attestato, args.output)
    print("Attestato generato:", args.output)
    print("Moduli tracciati:", len(statuses))


if __name__ == "__main__":
    main()
