#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLAN_PATH="planning/module_work_plan.md"
EXEC_PLAN_PATH=""
CHECK_ONLY=false

usage() {
  cat <<'USAGE'
Usage: tools/daily_workflow.sh [options]

Options:
  --check-only            Run refresh_module_reports in check mode (skip writing updates)
  --plan-path PATH        Path for the generated module plan output (default: planning/module_work_plan.md)
  --exec-plan-path PATH   Path for the executive plan output (omit to use generate_module_plan default)
  -h, --help              Show this help message
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only)
      CHECK_ONLY=true
      ;;
    --plan-path)
      [[ $# -ge 2 ]] || { echo "Missing argument for --plan-path" >&2; exit 1; }
      PLAN_PATH="$2"
      shift
      ;;
    --exec-plan-path)
      [[ $# -ge 2 ]] || { echo "Missing argument for --exec-plan-path" >&2; exit 1; }
      EXEC_PLAN_PATH="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
cd "$PROJECT_ROOT"

log_phase() {
  local message="$1"
  echo "[daily_workflow] $message"
}

run_phase() {
  local name="$1"
  shift
  log_phase "Starting: $name"
  local start_time end_time duration
  start_time=$(date +%s)

  if "$@"; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    log_phase "Completed: $name (duration: ${duration}s)"
  else
    local status=$?
    log_phase "$name failed with exit code $status"
    exit "$status"
  fi
}

if [[ "$CHECK_ONLY" == true ]]; then
  run_phase "Refresh module reports (--check)" python tools/refresh_module_reports.py --check
else
  run_phase "Refresh module reports (--write)" python tools/refresh_module_reports.py --write
fi

plan_command=(python tools/generate_module_plan.py --output "$PLAN_PATH")
if [[ -n "${EXEC_PLAN_PATH:-}" ]]; then
  plan_command+=(--executive-output "$EXEC_PLAN_PATH")
fi
run_phase "Generate module plan" "${plan_command[@]}"

run_phase "Run static analysis" tools/run_static_analysis.sh
