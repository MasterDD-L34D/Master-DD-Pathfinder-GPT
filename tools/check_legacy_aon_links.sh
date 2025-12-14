#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if rg -n "legacy\.aonprd\.com" src data; then
  echo "Legacy AoN URLs detected. Replace with aonprd.com (hint: rg \"legacy.aonprd.com\" src data)." >&2
  exit 1
fi

echo "No legacy.aonprd.com URLs found."
