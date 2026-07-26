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
     - make PYTEST_E2E_WORKERS=<workers> test-e2e

Parallel suite logs are written to .tmp/test-logs/<timestamp>/.
The legacy pytest browser smoke suite defaults to one internal worker inside
this already-parallel gate; override PYTEST_E2E_WORKERS to raise it.
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
  local log_name
  local log_file
  local status_file
  local start_ts

  log_name="$(printf '%s' "${name}" | tr ' /' '__' | tr -cd 'A-Za-z0-9_.-')"
  log_file="${LOG_DIR}/${log_name}.log"
  status_file="${LOG_DIR}/${log_name}.status"
  start_ts="$(date +%s)"

  section "Starting ${name}: $*"
  printf 'Log: %s\n' "${log_file}"
  (
    command_start="$(date +%s)"
    if "$@"; then
      command_status=0
    else
      command_status="$?"
    fi
    command_end="$(date +%s)"
    printf '%s %s\n' "${command_status}" "$((command_end - command_start))" >"${status_file}"
    exit "${command_status}"
  ) >"${log_file}" 2>&1 &
  PARALLEL_PIDS+=("$!")
  PARALLEL_NAMES+=("${name}")
  PARALLEL_LOGS+=("${log_file}")
  PARALLEL_STATUS_FILES+=("${status_file}")
  PARALLEL_STARTS+=("${start_ts}")
}

format_duration() {
  local seconds="$1"
  printf '%dm%02ds' "$((seconds / 60))" "$((seconds % 60))"
}

cd "${ROOT_DIR}"

LOG_DIR="${ROOT_DIR}/.tmp/test-logs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "${LOG_DIR}"

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
PARALLEL_LOGS=()
PARALLEL_STATUS_FILES=()
PARALLEL_STARTS=()
PARALLEL_STATUSES=()
PARALLEL_DURATIONS=()

run_parallel "Python static tests" make test-static

if [[ "${RUN_PLAYWRIGHT}" -eq 1 ]]; then
  run_parallel "Frontend Playwright tests" npm --prefix "${FRONTEND_DIR}" run test:e2e
fi

if [[ "${RUN_INTEGRATION}" -eq 1 ]]; then
  run_parallel "Frontend integration tests" npm --prefix "${FRONTEND_DIR}" run test:integration
fi

if [[ "${RUN_LEGACY_E2E}" -eq 1 ]]; then
  LEGACY_E2E_WORKERS="${PYTEST_E2E_WORKERS:-1}"
  run_parallel "Legacy pytest E2E tests" make "PYTEST_E2E_WORKERS=${LEGACY_E2E_WORKERS}" test-e2e
fi

FAILED=0
for i in "${!PARALLEL_PIDS[@]}"; do
  name="${PARALLEL_NAMES[$i]}"
  pid="${PARALLEL_PIDS[$i]}"
  log_file="${PARALLEL_LOGS[$i]}"
  status_file="${PARALLEL_STATUS_FILES[$i]}"
  start_ts="${PARALLEL_STARTS[$i]}"
  if wait "${pid}"; then
    status=0
    section "${name} passed"
  else
    status="$?"
    section "${name} failed with exit ${status}"
    printf 'Last 80 log lines from %s:\n' "${log_file}"
    tail -n 80 "${log_file}" || true
    FAILED=1
  fi
  if [[ -f "${status_file}" ]]; then
    read -r recorded_status duration <"${status_file}"
    status="${recorded_status:-${status}}"
  else
    end_ts="$(date +%s)"
    duration="$((end_ts - start_ts))"
  fi
  PARALLEL_STATUSES+=("${status}")
  PARALLEL_DURATIONS+=("$(format_duration "${duration}")")
done

section "Parallel suite summary"
printf '%-32s %-8s %-8s %s\n' "Suite" "Status" "Duration" "Log"
for i in "${!PARALLEL_NAMES[@]}"; do
  name="${PARALLEL_NAMES[$i]}"
  status="${PARALLEL_STATUSES[$i]}"
  duration="${PARALLEL_DURATIONS[$i]}"
  log_file="${PARALLEL_LOGS[$i]}"
  if [[ "${status}" -eq 0 ]]; then
    label="passed"
  else
    label="failed"
  fi
  printf '%-32s %-8s %-8s %s\n' "${name}" "${label}" "${duration}" "${log_file}"
done

if [[ "${FAILED}" -ne 0 ]]; then
  section "One or more selected checks failed"
  exit 1
fi

section "All selected checks passed"
