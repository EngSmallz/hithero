#!/usr/bin/env bash

# Start the local FastAPI and Vite development servers with matching origins.
# Stop both with Ctrl-C. Override LOCAL_BACKEND_ORIGIN, LOCAL_FRONTEND_HOST,
# LOCAL_FRONTEND_PORT, LOCAL_SECRET_KEY, or LOCAL_BACKEND_RELOAD when needed.

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_HOST="${LOCAL_BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${LOCAL_BACKEND_PORT:-8000}"
FRONTEND_HOST="${LOCAL_FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${LOCAL_FRONTEND_PORT:-5173}"
BACKEND_ORIGIN="${LOCAL_BACKEND_ORIGIN:-http://${BACKEND_HOST}:${BACKEND_PORT}}"
SECRET_KEY="${LOCAL_SECRET_KEY:-dev-secret}"
DATABASE_URL="${LOCAL_DATABASE_URL:-sqlite:///./.local/hithero-dev.sqlite}"
PYTHON_BIN="${LOCAL_PYTHON_BIN:-/opt/miniconda3/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="${LOCAL_PYTHON_FALLBACK:-$(command -v python3)}"
fi

backend_pid=""
frontend_pid=""

cleanup() {
  trap - EXIT INT TERM
  if [[ -n "${backend_pid}" ]] && kill -0 "${backend_pid}" 2>/dev/null; then
    kill "${backend_pid}" 2>/dev/null || true
  fi
  if [[ -n "${frontend_pid}" ]] && kill -0 "${frontend_pid}" 2>/dev/null; then
    kill "${frontend_pid}" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
}

trap cleanup EXIT INT TERM

cd "${ROOT_DIR}"
mkdir -p .local

echo "Starting backend at http://${BACKEND_HOST}:${BACKEND_PORT}"
if [[ "${LOCAL_BACKEND_RELOAD:-0}" == "1" ]]; then
  APP_ENV=development \
  SECRET_KEY="${SECRET_KEY}" \
  DATABASE_URL="${DATABASE_URL}" \
  "${PYTHON_BIN}" -m uvicorn app:app --reload --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
else
  APP_ENV=development \
  SECRET_KEY="${SECRET_KEY}" \
  DATABASE_URL="${DATABASE_URL}" \
  "${PYTHON_BIN}" -m uvicorn app:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
fi
backend_pid=$!

echo "Starting frontend at http://${FRONTEND_HOST}:${FRONTEND_PORT}"
(
  cd frontend
  PUBLIC_BACKEND_ORIGIN="${BACKEND_ORIGIN}" \
    PUBLIC_RECAPTCHA_MODE="${PUBLIC_RECAPTCHA_MODE:-mock}" \
    npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}"
) &
frontend_pid=$!

echo "Both servers are running. Press Ctrl-C to stop them."

while kill -0 "${backend_pid}" 2>/dev/null && kill -0 "${frontend_pid}" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "${backend_pid}" 2>/dev/null; then
  echo "Backend exited; stopping frontend." >&2
else
  echo "Frontend exited; stopping backend." >&2
fi
exit 1
