import argparse
import datetime
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

MODULE_HEADING_RE = re.compile(
    r"^####\s+(?P<module>.+?)\s+—\s+Owner:\s+(?P<owner>.+?)(?:\s+—\s+Checkpoint:\s+(?P<checkpoint>\d{4}-\d{2}-\d{2}))?\s*$"
)
STORY_ID_RE = re.compile(r"^[A-Z]{2,}-[A-Z]{2,}-\d{2,}")


class Violation:
    def __init__(self, kind: str, detail: str, story_id: str | None = None, module: str | None = None):
        self.kind = kind
        self.detail = detail
        self.story_id = story_id
        self.module = module

    def to_dict(self) -> Dict[str, str | None]:
        return {
            "kind": self.kind,
            "detail": self.detail,
            "story_id": self.story_id,
            "module": self.module,
        }


def parse_owner_sections(lines: List[str]) -> Tuple[Dict[str, dict], Dict[str, str]]:
    module_data: Dict[str, dict] = {}
    story_to_module: Dict[str, str] = {}
    current_module: str | None = None

    for idx, line in enumerate(lines):
        heading = MODULE_HEADING_RE.match(line)
        if heading:
            current_module = heading.group("module").strip()
            module_data[current_module] = {
                "owner": heading.group("owner").strip(),
                "checkpoint": heading.group("checkpoint"),
                "stories": {},
            }
            continue

        if line.startswith("### ") or (line.startswith("#### ") and not heading):
            current_module = None
            continue

        if current_module and line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells or not STORY_ID_RE.match(cells[0]):
                continue
            story_id = cells[0]
            status = cells[-1]
            module_data[current_module]["stories"][story_id] = {
                "status": status,
                "line": idx + 1,
            }
            story_to_module[story_id] = current_module

    return module_data, story_to_module


def parse_summary_table(lines: List[str], heading: str) -> List[dict]:
    rows: List[dict] = []
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            header_idx = idx + 1
            while header_idx < len(lines) and not lines[header_idx].startswith("|"):
                if lines[header_idx].startswith("#"):
                    header_idx = None
                    break
                header_idx += 1

            if header_idx is None or header_idx >= len(lines):
                continue

            data_idx = header_idx + 2  # skip header and separator rows
            while data_idx < len(lines) and lines[data_idx].startswith("|"):
                cells = [cell.strip() for cell in lines[data_idx].strip().strip("|").split("|")]
                if cells and STORY_ID_RE.match(cells[0]):
                    rows.append(
                        {
                            "story_id": cells[0],
                            "origin": cells[1] if len(cells) > 1 else "",
                            "status": cells[2] if len(cells) > 2 else "",
                        }
                    )
                data_idx += 1
    return rows


def load_plan(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def is_done(status: str) -> bool:
    return "done" in status.lower()


def validate(plan_path: Path) -> Tuple[List[Violation], dict]:
    lines = load_plan(plan_path)
    module_data, story_to_module = parse_owner_sections(lines)

    summary_moduli_critici = parse_summary_table(lines, "### Moduli critici")
    summary_altri_moduli = parse_summary_table(lines, "### Altri moduli")

    violations: List[Violation] = []
    today = datetime.date.today()

    def check_summary_rows(rows: List[dict]):
        for row in rows:
            story_id = row.get("story_id", "")
            module = story_to_module.get(story_id)
            if not module:
                violations.append(
                    Violation(
                        kind="owner-missing",
                        detail=f"Story {story_id} non associata ad alcun modulo con Owner.",
                        story_id=story_id,
                        module=None,
                    )
                )
                continue

            module_info = module_data.get(module, {})
            owner = module_info.get("owner")
            if not owner:
                violations.append(
                    Violation(
                        kind="owner-missing",
                        detail=f"Modulo {module} privo di Owner assegnato (story {story_id}).",
                        story_id=story_id,
                        module=module,
                    )
                )

            status = row.get("status", "")
            if not is_done(status):
                violations.append(
                    Violation(
                        kind="status-not-done",
                        detail=f"Story {story_id} del modulo {module} non è marcata Done (stato: {status}).",
                        story_id=story_id,
                        module=module,
                    )
                )

            if "CHK" in story_id:
                checkpoint_date = module_info.get("checkpoint")
                if checkpoint_date:
                    checkpoint = datetime.date.fromisoformat(checkpoint_date)
                    if checkpoint < today and not is_done(status):
                        violations.append(
                            Violation(
                                kind="checkpoint-expired",
                                detail=f"Checkpoint {story_id} del modulo {module} scaduto il {checkpoint_date} e non Done.",
                                story_id=story_id,
                                module=module,
                            )
                        )

    check_summary_rows(summary_moduli_critici)
    check_summary_rows(summary_altri_moduli)

    # Additional guard: ensure checkpoint stories parsed in sections are Done
    for module, info in module_data.items():
        for story_id, meta in info.get("stories", {}).items():
            if "CHK" in story_id and not is_done(meta.get("status", "")):
                violations.append(
                    Violation(
                        kind="checkpoint-not-done",
                        detail=f"Checkpoint {story_id} nel modulo {module} non è Done (riga {meta.get('line')}).",
                        story_id=story_id,
                        module=module,
                    )
                )

    report = {
        "plan": str(plan_path),
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "violations": [v.to_dict() for v in violations],
        "modules_with_owner": len(module_data),
        "stories_checked": len(summary_moduli_critici) + len(summary_altri_moduli),
    }

    return violations, report


def render_report(report: dict, as_json: bool) -> str:
    if as_json:
        return json.dumps(report, ensure_ascii=False, indent=2)

    lines = ["## Risultato verifica owner e checkpoint", "", f"Piano: `{report['plan']}`", ""]
    if report["violations"]:
        lines.append("### Violazioni trovate")
        for violation in report["violations"]:
            module = violation.get("module") or "(sconosciuto)"
            story = violation.get("story_id") or "(n/a)"
            lines.append(f"- **{violation['kind']}** — Modulo: {module}, Story: {story}. {violation['detail']}")
    else:
        lines.append("Nessuna violazione rilevata: tutti i moduli hanno owner e checkpoint Done.")

    lines.append("")
    lines.append(f"Moduli con owner: {report['modules_with_owner']}")
    lines.append(f"Storie controllate: {report['stories_checked']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica owner e checkpoint nel piano dei moduli")
    parser.add_argument(
        "--plan",
        default="planning/module_work_plan.md",
        help="Percorso al file di piano da verificare",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Formato di output del report",
    )
    args = parser.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise SystemExit(f"File di piano non trovato: {plan_path}")

    violations, report = validate(plan_path)
    print(render_report(report, as_json=args.format == "json"))

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
