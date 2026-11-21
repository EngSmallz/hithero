#!/usr/bin/env bash
# Start the local test SQL Server and load the seed data (BE1-3).
#   scripts/test_db.sh         start (or reuse) the container and reseed
#   scripts/test_db.sh down    stop and remove the container
# Needs Docker, and Microsoft ODBC Driver 18 for SQL Server on this machine.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" == "down" ]]; then
  docker compose -f compose.test.yaml down -v
  exit 0
fi

docker compose -f compose.test.yaml up -d --wait
python -m tests.seed
echo "Test database ready. Run the tests with: TEST_DATABASE=1 pytest"
