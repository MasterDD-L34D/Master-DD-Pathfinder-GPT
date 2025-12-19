#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Running black --check..."
python -m black --check src tests tools || {
  echo "black check failed. Run 'python -m black src tests tools' to format." >&2
  exit 1
}

echo "Checking for legacy AoN URLs..."
./tools/check_legacy_aon_links.sh

echo "Running python -m compileall..."
python -m compileall src tests

echo "Cleaning up compiled bytecode artifacts..."
find src tests -name "__pycache__" -type d -prune -exec rm -rf {} +

echo "Static analysis completed successfully."
