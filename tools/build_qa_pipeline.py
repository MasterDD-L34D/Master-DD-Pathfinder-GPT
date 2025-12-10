"""Orchestrate QA passes for generated build payloads.

This script loads build payloads collected via ``tools/generate_build_db.py``
and runs a QA pipeline across multiple services:
- Ruling Expert: validates and tags ``ruling_badge``
- MinMax Builder: runs benchmark/QA checks
- Narrative hooks (optional): ``/export_arc_to_build`` and ``/ruling_check``

Each step records PASS/FAIL with a rationale. Any failure marks the build as
``invalid`` and stops subsequent export actions.
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

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "build_file": self.build_file,
            "class": self.class_name,
            "level": self.level,
            "spec_id": self.spec_id,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass
class QaPipelineConfig:
    ruling_expert_url: str | None
    minmax_builder_url: str | None
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
            narrative_result = self._run_narrative_hooks(payload)
            steps.append(narrative_result)
            if narrative_result.status == "FAIL":
                report.status = "invalid"

        report.steps = steps
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
            badge = None
            response = result.details or {}
            if isinstance(response, Mapping):
                badge = response.get("ruling_badge") or response.get("badge")
            reason = "Badge validato" if badge else "Validazione completata"
            details = dict(result.details or {})
            if badge:
                details["ruling_badge"] = badge
            return StepResult(
                name="ruling_expert",
                status="PASS",
                reason=reason,
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

    def _run_narrative_hooks(self, payload: Mapping[str, Any]) -> StepResult:
        export_url = self.config.narrative_export_url
        ruling_url = self.config.narrative_ruling_check_url

        if not export_url and not ruling_url:
            return StepResult(
                name="narrative_hooks",
                status="PASS",
                reason="Step narrativo disattivato o nessun endpoint fornito",
            )

        details: dict[str, Any] = {}

        if export_url:
            export_result = self._post_json(
                url=export_url,
                payload={"build": payload},
                step_name="export_arc_to_build",
            )
            details["export_arc_to_build"] = export_result.to_dict()
            if export_result.status == "FAIL":
                return StepResult(
                    name="narrative_hooks",
                    status="FAIL",
                    reason=f"export_arc_to_build fallito: {export_result.reason}",
                    details=details,
                )

        if ruling_url:
            ruling_result = self._post_json(
                url=ruling_url,
                payload={"build": payload},
                step_name="ruling_check",
            )
            details["ruling_check"] = ruling_result.to_dict()
            if ruling_result.status == "FAIL":
                return StepResult(
                    name="narrative_hooks",
                    status="FAIL",
                    reason=f"ruling_check fallito: {ruling_result.reason}",
                    details=details,
                )

        return StepResult(
            name="narrative_hooks",
            status="PASS",
            reason="Hook narrativi completati",
            details=details or None,
        )

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
