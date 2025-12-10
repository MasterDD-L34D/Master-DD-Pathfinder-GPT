"""Orchestrate QA passes for generated build payloads.

This script loads build payloads collected via ``tools/generate_build_db.py``
and runs a QA pipeline across multiple services:
- Ruling Expert: validates and tags ``ruling_badge``
- MinMax Builder: runs benchmark/QA checks
- Narrative enrichment: fetches arc/theme from Taverna and exports it to MinMax
  before re-running QA and a narrative ruling check.

Each step records PASS/FAIL with a rationale. Any failure marks the build as
``invalid`` and stops subsequent export actions while logging the applied
changes.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

import httpx

DEFAULT_INDEX_PATH = Path("src/data/build_index.json")
DEFAULT_REPORT_PATH = Path("reports/build_qa_report.json")


def _normalize_badge_value(badge: object) -> str | None:
    if isinstance(badge, str):
        return badge.strip().lower() or None
    if isinstance(badge, Mapping):
        for key in ("badge", "label", "value"):
            candidate = badge.get(key)
            if isinstance(candidate, str):
                return candidate.strip().lower() or None
    return None


@dataclass
class StepResult:
    name: str
    status: str
    reason: str
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> Mapping[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "reason": self.reason,
        }
        if self.details is not None:
            data["details"] = self.details
        return data


@dataclass
class BuildReportEntry:
    build_file: str
    class_name: str
    level: int | None
    spec_id: str | None
    status: str = "valid"
    steps: list[StepResult] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "build_file": self.build_file,
            "class": self.class_name,
            "level": self.level,
            "spec_id": self.spec_id,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "changes": self.changes,
        }


@dataclass
class QaPipelineConfig:
    ruling_expert_url: str | None
    minmax_builder_url: str | None
    narrative_arc_url: str | None
    narrative_export_url: str | None
    narrative_ruling_check_url: str | None
    api_key: str | None
    timeout: float
    enable_narrative: bool


class QaPipeline:
    def __init__(self, client: httpx.Client, config: QaPipelineConfig) -> None:
        self.client = client
        self.config = config

    def run(
        self, payload: Mapping[str, Any], entry: Mapping[str, Any]
    ) -> BuildReportEntry:
        report = BuildReportEntry(
            build_file=str(entry.get("file")),
            class_name=str(entry.get("class")),
            level=entry.get("level"),
            spec_id=entry.get("spec_id"),
        )

        steps: list[StepResult] = []
        change_log: list[str] = []
        arc_context: Mapping[str, Any] | None = None

        ruling_result = self._run_ruling_expert(payload)
        steps.append(ruling_result)
        if ruling_result.status == "FAIL":
            report.status = "invalid"
            report.steps = steps
            return report

        builder_result = self._run_minmax_builder(payload)
        steps.append(builder_result)
        if builder_result.status == "FAIL":
            report.status = "invalid"
            report.steps = steps
            return report

        if self.config.enable_narrative:
            arc_result = self._fetch_narrative_arc(payload)
            steps.append(arc_result)
            change_log.extend(self._collect_change_log(arc_result.details))
            if arc_result.status == "FAIL":
                report.status = "invalid"
                report.steps = steps
                report.changes = change_log
                return report

            arc_context = arc_result.details if isinstance(arc_result.details, Mapping) else None

            export_result = self._export_arc_to_build(payload, arc_context)
            steps.append(export_result)
            change_log.extend(self._collect_change_log(export_result.details))
            if export_result.status == "FAIL":
                report.status = "invalid"
                report.steps = steps
                report.changes = change_log
                return report

            qa_result = self._run_post_import_qa(payload, arc_context)
            steps.append(qa_result)
            change_log.extend(self._collect_change_log(qa_result.details))
            if qa_result.status == "FAIL":
                report.status = "invalid"
                report.steps = steps
                report.changes = change_log
                return report

            ruling_check_result = self._run_narrative_ruling_check(
                payload, arc_context
            )
            steps.append(ruling_check_result)
            change_log.extend(self._collect_change_log(ruling_check_result.details))
            if ruling_check_result.status == "FAIL":
                report.status = "invalid"

        report.steps = steps
        report.changes = change_log
        return report

    def _run_ruling_expert(self, payload: Mapping[str, Any]) -> StepResult:
        if not self.config.ruling_expert_url:
            return StepResult(
                name="ruling_expert",
                status="FAIL",
                reason="Endpoint Ruling Expert non configurato",
            )

        result = self._post_json(
            url=self.config.ruling_expert_url,
            payload={"build": payload},
            step_name="ruling_expert",
        )
        if result.status == "PASS":
            response = result.details if isinstance(result.details, Mapping) else {}
            badge = response.get("ruling_badge") or response.get("badge")
            sources = response.get("sources") or response.get("fonti")
            violations = response.get("violations")
            if violations:
                return StepResult(
                    name="ruling_expert",
                    status="FAIL",
                    reason="Violazioni Ruling Expert: "
                    + "; ".join(map(str, violations)),
                    details=response,
                )

            normalized_badge = _normalize_badge_value(badge)
            if not normalized_badge:
                return StepResult(
                    name="ruling_expert",
                    status="FAIL",
                    reason="Badge Ruling Expert mancante o non conforme",
                    details=response or None,
                )

            details = dict(response)
            details["ruling_badge"] = normalized_badge
            if sources:
                details["sources"] = sources
            return StepResult(
                name="ruling_expert",
                status="PASS",
                reason=f"Badge validato ({normalized_badge})",
                details=details or None,
            )
        return result

    def _run_minmax_builder(self, payload: Mapping[str, Any]) -> StepResult:
        if not self.config.minmax_builder_url:
            return StepResult(
                name="minmax_builder",
                status="FAIL",
                reason="Endpoint MinMax Builder non configurato",
            )

        return self._post_json(
            url=self.config.minmax_builder_url,
            payload={"build": payload},
            step_name="minmax_builder",
        )

    def _fetch_narrative_arc(self, payload: Mapping[str, Any]) -> StepResult:
        if not self.config.narrative_arc_url:
            return StepResult(
                name="narrative_arc",
                status="FAIL",
                reason="Endpoint Taverna/Narrative per l'arco non configurato",
            )

        arc_result = self._post_json(
            url=self.config.narrative_arc_url,
            payload={"build": payload},
            step_name="narrative_arc",
        )

        if arc_result.status != "PASS":
            return arc_result

        details = (
            dict(arc_result.details)
            if isinstance(arc_result.details, Mapping)
            else {}
        )
        arc = self._extract_arc(details)
        themes = self._extract_themes(details)
        if not arc or not themes:
            return StepResult(
                name="narrative_arc",
                status="FAIL",
                reason="Arco o tema assente nella risposta narrativa",
                details=details or None,
            )

        details["arc"] = arc
        details["themes"] = themes
        change_log = self._collect_change_log(details)
        if change_log:
            details["changes_applied"] = change_log

        return StepResult(
            name="narrative_arc",
            status="PASS",
            reason=f"Arco e tema ricevuti ({arc})",
            details=details or None,
        )

    def _export_arc_to_build(
        self, payload: Mapping[str, Any], arc_details: Mapping[str, Any] | None
    ) -> StepResult:
        if not self.config.narrative_export_url:
            return StepResult(
                name="export_arc_to_build",
                status="FAIL",
                reason="Endpoint /export_arc_to_build non configurato",
            )

        export_payload: dict[str, Any] = {"build": payload}
        if arc_details:
            export_payload.update(
                {
                    "arc": arc_details.get("arc"),
                    "themes": arc_details.get("themes"),
                    "pg_id": arc_details.get("pg_id")
                    or payload.get("pg_id")
                    or payload.get("spec_id"),
                }
            )

        export_result = self._post_json(
            url=self.config.narrative_export_url,
            payload=export_payload,
            step_name="export_arc_to_build",
        )

        if export_result.status != "PASS":
            return export_result

        details = (
            dict(export_result.details)
            if isinstance(export_result.details, Mapping)
            else {}
        )
        change_log = self._collect_change_log(details)
        if change_log:
            details["changes_applied"] = change_log

        return StepResult(
            name="export_arc_to_build",
            status="PASS",
            reason="Arco/tema inviati a MinMax",
            details=details or None,
        )

    def _run_post_import_qa(
        self, payload: Mapping[str, Any], arc_details: Mapping[str, Any] | None
    ) -> StepResult:
        if not self.config.minmax_builder_url:
            return StepResult(
                name="post_import_qa",
                status="FAIL",
                reason="Endpoint MinMax Builder non configurato",
            )

        qa_items = ["CA", "PF", "TS", "skill", "equip", "incantesimi"]
        request_payload: dict[str, Any] = {
            "build": payload,
            "qa_checklist": qa_items,
            "phase": "post_import",
        }
        if arc_details:
            request_payload["arc"] = arc_details

        qa_result = self._post_json(
            url=self.config.minmax_builder_url,
            payload=request_payload,
            step_name="post_import_qa",
        )

        if qa_result.status != "PASS":
            return qa_result

        details = (
            dict(qa_result.details)
            if isinstance(qa_result.details, Mapping)
            else {}
        )
        issue_key, issue_value = self._extract_inconsistencies(details)
        if issue_key:
            summary = issue_value if isinstance(issue_value, str) else str(issue_value)
            return StepResult(
                name="post_import_qa",
                status="FAIL",
                reason=f"Incongruenze QA ({issue_key}): {summary}",
                details=details or None,
            )

        change_log = self._collect_change_log(details)
        if change_log:
            details["changes_applied"] = change_log

        return StepResult(
            name="post_import_qa",
            status="PASS",
            reason="Checklist CA/PF/TS/skill/equip/incantesimi OK",
            details=details or None,
        )

    def _run_narrative_ruling_check(
        self, payload: Mapping[str, Any], arc_details: Mapping[str, Any] | None
    ) -> StepResult:
        if not self.config.narrative_ruling_check_url:
            return StepResult(
                name="ruling_check",
                status="FAIL",
                reason="Endpoint ruling_check narrativo non configurato",
            )

        request_payload: dict[str, Any] = {"build": payload}
        if arc_details:
            request_payload["arc"] = arc_details

        ruling_result = self._post_json(
            url=self.config.narrative_ruling_check_url,
            payload=request_payload,
            step_name="ruling_check",
        )

        if ruling_result.status != "PASS":
            return ruling_result

        details = (
            dict(ruling_result.details)
            if isinstance(ruling_result.details, Mapping)
            else {}
        )
        issue_key, issue_value = self._extract_inconsistencies(details)
        if issue_key:
            summary = issue_value if isinstance(issue_value, str) else str(issue_value)
            return StepResult(
                name="ruling_check",
                status="FAIL",
                reason=f"Incongruenze narrative rilevate ({issue_key}): {summary}",
                details=details or None,
            )

        change_log = self._collect_change_log(details)
        if change_log:
            details["changes_applied"] = change_log

        return StepResult(
            name="ruling_check",
            status="PASS",
            reason="Ruling narrativo allineato con l'import",
            details=details or None,
        )

    def _extract_arc(self, details: Mapping[str, Any]) -> str | None:
        for key in ("arc", "arco", "protagonist_arc", "story_arc"):
            value = details.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_themes(self, details: Mapping[str, Any]) -> list[str] | None:
        theme_keys = ("themes", "tema", "temi", "story_themes")
        for key in theme_keys:
            value = details.get(key)
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            if isinstance(value, list) and value:
                normalized = [str(item).strip() for item in value if str(item).strip()]
                if normalized:
                    return normalized
        return None

    def _extract_inconsistencies(
        self, details: Mapping[str, Any]
    ) -> tuple[str | None, Any]:
        for key in (
            "incongruenze",
            "inconsistencies",
            "issues",
            "qa_failures",
        ):
            value = details.get(key)
            if isinstance(value, list) and value:
                return key, value
            if isinstance(value, str) and value.strip():
                return key, value

        qa_status = details.get("qa_status")
        if isinstance(qa_status, str) and qa_status.lower() not in {"ok", "pass", "passed"}:
            return "qa_status", qa_status

        return None, None

    def _collect_change_log(self, details: Mapping[str, Any] | None) -> list[str]:
        if not details:
            return []

        collected: list[str] = []
        for key in ("changes", "modifiche", "tratti", "traits", "background", "motivazioni", "motivations"):
            value = details.get(key)
            if isinstance(value, str) and value.strip():
                collected.append(f"{key}: {value.strip()}")
            elif isinstance(value, list):
                for item in value:
                    item_text = str(item).strip()
                    if item_text:
                        collected.append(f"{key}: {item_text}")
            elif isinstance(value, Mapping):
                for sub_key, sub_val in value.items():
                    sub_text = str(sub_val).strip()
                    if sub_text:
                        collected.append(f"{key}.{sub_key}: {sub_text}")

        return collected

    def _post_json(
        self, url: str, payload: Mapping[str, Any], step_name: str
    ) -> StepResult:
        try:
            response = self.client.post(url, json=payload, timeout=self.config.timeout)
        except (
            httpx.HTTPError
        ) as exc:  # pragma: no cover - network failures are runtime dependent
            return StepResult(
                name=step_name,
                status="FAIL",
                reason=f"Richiesta fallita: {exc}",
            )

        if response.status_code >= 400:
            snippet = response.text[:200]
            return StepResult(
                name=step_name,
                status="FAIL",
                reason=f"HTTP {response.status_code}: {snippet}",
            )

        response_details: Mapping[str, Any] | None
        try:
            response_details = response.json()
        except ValueError:
            response_details = {"raw_response": response.text}

        return StepResult(
            name=step_name,
            status="PASS",
            reason="OK",
            details=response_details,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Esegue la pipeline di QA sulle build generate (badge Ruling, MinMax, "
            "hook narrativi opzionali) e produce un report di esito."
        )
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Indice delle build generate da analizzare (default: src/data/build_index.json)",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Percorso di output per il report QA (default: reports/build_qa_report.json)",
    )
    parser.add_argument(
        "--ruling-expert-url",
        dest="ruling_expert_url",
        type=str,
        help="Endpoint REST del Ruling Expert per validare/taggare il ruling_badge",
    )
    parser.add_argument(
        "--minmax-builder-url",
        dest="minmax_builder_url",
        type=str,
        help="Endpoint REST del MinMax Builder per benchmark/QA",
    )
    parser.add_argument(
        "--narrative-export-url",
        dest="narrative_export_url",
        type=str,
        help="Endpoint opzionale per l'hook narrativo /export_arc_to_build",
    )
    parser.add_argument(
        "--narrative-arc-url",
        dest="narrative_arc_url",
        type=str,
        help="Endpoint Taverna/Narrative per recuperare arco e tema del PG",
    )
    parser.add_argument(
        "--narrative-ruling-check-url",
        dest="narrative_ruling_check_url",
        type=str,
        help="Endpoint opzionale per l'hook narrativo /ruling_check",
    )
    parser.add_argument(
        "--enable-narrative",
        action="store_true",
        help="Abilita l'esecuzione degli hook narrativi se gli endpoint sono configurati",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        type=str,
        help="API key da inviare come header x-api-key verso tutti gli endpoint",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout (secondi) per ogni chiamata HTTP",
    )
    parser.add_argument(
        "--classes",
        dest="filter_classes",
        nargs="*",
        help="Elenco di classi da includere (case-insensitive)",
    )
    parser.add_argument(
        "--levels",
        dest="filter_levels",
        nargs="*",
        type=int,
        help="Checkpoint di livello da includere",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        help="Numero massimo di build/snapshot da processare dopo i filtri",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Numero di build/snapshot da saltare prima di applicare max-items",
    )
    return parser.parse_args()


def load_index(index_path: Path) -> Mapping[str, Any]:
    if not index_path.exists():
        raise FileNotFoundError(f"Indice non trovato: {index_path}")
    with index_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def filter_entries(
    entries: Iterable[Mapping[str, Any]],
    classes: Iterable[str] | None,
    levels: Iterable[int] | None,
    max_items: int | None,
    offset: int,
) -> list[Mapping[str, Any]]:
    normalized_classes = {cls.lower() for cls in classes} if classes else None
    normalized_levels = set(levels) if levels else None

    filtered: list[Mapping[str, Any]] = []
    for entry in entries:
        if (
            normalized_classes
            and str(entry.get("class", "")).lower() not in normalized_classes
        ):
            continue
        if normalized_levels and entry.get("level") not in normalized_levels:
            continue
        filtered.append(entry)

    window = filtered[offset:]
    if max_items is not None and max_items >= 0:
        window = window[:max_items]
    return window


def load_payload(payload_path: Path) -> Mapping[str, Any]:
    with payload_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_report(report: Mapping[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    index = load_index(args.index_path)
    entries = index.get("entries", [])

    filtered_entries = filter_entries(
        entries=entries,
        classes=args.filter_classes,
        levels=args.filter_levels,
        max_items=args.max_items,
        offset=args.offset,
    )

    headers: dict[str, str] = {}
    if args.api_key:
        headers["x-api-key"] = args.api_key

    config = QaPipelineConfig(
        ruling_expert_url=args.ruling_expert_url,
        minmax_builder_url=args.minmax_builder_url,
        narrative_arc_url=args.narrative_arc_url,
        narrative_export_url=args.narrative_export_url,
        narrative_ruling_check_url=args.narrative_ruling_check_url,
        api_key=args.api_key,
        timeout=args.timeout,
        enable_narrative=args.enable_narrative,
    )

    report_entries: list[BuildReportEntry] = []
    with httpx.Client(headers=headers) as client:
        pipeline = QaPipeline(client=client, config=config)
        for entry in filtered_entries:
            payload_path = Path(entry.get("file", ""))
            try:
                payload = load_payload(payload_path)
            except FileNotFoundError:
                logging.error("Payload mancante: %s", payload_path)
                missing = BuildReportEntry(
                    build_file=str(payload_path),
                    class_name=str(entry.get("class")),
                    level=entry.get("level"),
                    spec_id=entry.get("spec_id"),
                    status="invalid",
                    steps=[
                        StepResult(
                            name="load_payload",
                            status="FAIL",
                            reason="File non trovato",
                        )
                    ],
                )
                report_entries.append(missing)
                continue

            logging.info(
                "Eseguo QA pipeline per %s (livello %s)",
                entry.get("class"),
                entry.get("level"),
            )
            report_entries.append(pipeline.run(payload=payload, entry=entry))

    report_payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "index_path": str(args.index_path),
        "report_path": str(args.report_path),
        "filters": {
            "classes": args.filter_classes,
            "levels": args.filter_levels,
            "max_items": args.max_items,
            "offset": args.offset,
        },
        "entries": [entry.to_dict() for entry in report_entries],
    }

    write_report(report_payload, args.report_path)
    logging.info("Report QA scritto in %s", args.report_path)


if __name__ == "__main__":
    main()
