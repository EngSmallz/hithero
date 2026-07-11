# P0-03: Define `scripts/run-all-tests.sh` As The Canonical Modernization Gate

## Problem

The repository has a full verification script that runs the important checks in the intended order and parallelizes the slow suites. The modernization effort needs one trusted command that developers and agents use before calling work done.

## Scope

- Treat `scripts/run-all-tests.sh` as the canonical full modernization gate.
- Document the full and quick commands in README or local development docs.
- Ensure the script's ordering prevents unsafe build/dev-server races while preserving parallel E2E execution.
- Make failures easy to attribute to the suite that failed.

## Acceptance Criteria

- Documentation clearly says to run `scripts/run-all-tests.sh` before merge/release.
- `--quick` is documented for fast local feedback.
- The full script exits non-zero if any selected suite fails.
- The script can be run from the repository root without extra tribal knowledge.
- The script remains compatible with the P0-02 parallel determinism work.

## Verification

- `scripts/run-all-tests.sh --quick`
- `scripts/run-all-tests.sh`
- Review README/docs for the documented gate.
