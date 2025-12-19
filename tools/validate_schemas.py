#!/usr/bin/env python3
"""Validate JSON Schema files shipped with the repository.

The script loads every `*.schema.json` file under the `schemas/` directory and
runs `Draft202012Validator.check_schema` to catch structural mistakes early in
CI. It exits with a non-zero status code when any schema is invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


def iter_schema_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.glob("*.schema.json")):
        if path.is_file():
            yield path


def validate_schema(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(payload)
    except SchemaError as exc:
        return f"{path}: schema non valida — {exc.message}"
    except Exception as exc:  # pragma: no cover - defensive logging
        return f"{path}: errore di lettura/parse — {exc}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository JSON schemas")
    parser.add_argument(
        "--schemas-dir",
        type=Path,
        default=Path("schemas"),
        help="Directory contenente i file *.schema.json (default: schemas)",
    )
    args = parser.parse_args()

    errors = [issue for schema in iter_schema_files(args.schemas_dir) if (issue := validate_schema(schema))]

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Tutti gli schemi in {args.schemas_dir} sono validi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
