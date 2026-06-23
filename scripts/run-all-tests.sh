#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

RUN_FORMAT=1
RUN_FRONTEND=1
RUN_PLAYWRIGHT=1
RUN_INTEGRATION=1
RUN_LEGACY_E2E=1

usage() {
  cat <<'EOF'
Usage: scripts/run-all-tests.sh [options]

Runs the project verification suite from the repository root.

Options:
  --quick              Run static/backend checks and frontend check/lint only.
  --no-format         Skip npm run format.
  --no-frontend       Skip frontend format/check/lint.
  --no-playwright     Skip full frontend Playwright tests.
  --no-integration    Skip real-stack integration tests.
  --no-legacy-e2e     Skip legacy pytest E2E tests.
  -h, --help          Show this help.

Default sequence:
  1. frontend npm run format
  2. frontend npm run check
  3. frontend npm run lint
  4. Run selected slow suites in parallel:
     - make test-static
     - frontend npm run test:e2e
     - frontend npm run test:integration
     - make test-e2e
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --quick)
      RUN_FORMAT=0
      RUN_PLAYWRIGHT=0
      RUN_INTEGRATION=0
      RUN_LEGACY_E2E=0
      ;;
    --no-format)
      RUN_FORMAT=0
      ;;
    --no-frontend)
      RUN_FORMAT=0
      RUN_FRONTEND=0
      ;;
    --no-playwright)
      RUN_PLAYWRIGHT=0
      ;;
    --no-integration)
      RUN_INTEGRATION=0
      ;;
    --no-legacy-e2e)
      RUN_LEGACY_E2E=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

section() {
  printf '\n\033[1;36m==> %s\033[0m\n' "$*"
}

run() {
  section "$*"
  "$@"
}

run_parallel() {
  local name="$1"
  shift

  section "Starting ${name}: $*"
  "$@" &
  PARALLEL_PIDS+=("$!")
  PARALLEL_NAMES+=("${name}")
}

cd "${ROOT_DIR}"

if [[ "${RUN_FRONTEND}" -eq 1 ]]; then
  if [[ "${RUN_FORMAT}" -eq 1 ]]; then
    run npm --prefix "${FRONTEND_DIR}" run format
  fi

  run npm --prefix "${FRONTEND_DIR}" run check
  run npm --prefix "${FRONTEND_DIR}" run lint
fi

if [[ "${RUN_PLAYWRIGHT}" -eq 1 && "${RUN_INTEGRATION}" -eq 1 ]]; then
  run npm --prefix "${FRONTEND_DIR}" run build
  export PLAYWRIGHT_SKIP_BUILD=1
fi

PARALLEL_PIDS=()
PARALLEL_NAMES=()

run_parallel "Python static tests" make test-static

if [[ "${RUN_PLAYWRIGHT}" -eq 1 ]]; then
  run_parallel "Frontend Playwright tests" npm --prefix "${FRONTEND_DIR}" run test:e2e
fi

if [[ "${RUN_INTEGRATION}" -eq 1 ]]; then
  run_parallel "Frontend integration tests" npm --prefix "${FRONTEND_DIR}" run test:integration
fi

if [[ "${RUN_LEGACY_E2E}" -eq 1 ]]; then
  run_parallel "Legacy pytest E2E tests" make test-e2e
fi

FAILED=0
for i in "${!PARALLEL_PIDS[@]}"; do
  name="${PARALLEL_NAMES[$i]}"
  pid="${PARALLEL_PIDS[$i]}"
  if wait "${pid}"; then
    section "${name} passed"
  else
    status="$?"
    section "${name} failed with exit ${status}"
    FAILED=1
  fi
done

if [[ "${FAILED}" -ne 0 ]]; then
  section "One or more selected checks failed"
  exit 1
fi

section "All selected checks passed"
