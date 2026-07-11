# P2-12: Clean Test Warning Noise

## Problem

The test suite currently emits SQLAlchemy and Pydantic deprecation warnings. They are not release blockers, but they weaken the signal of the verification gate and can hide new warnings.

## Scope

- Address SQLAlchemy deprecation warnings where straightforward.
- Address Pydantic deprecation warnings where straightforward.
- If a warning cannot be fixed safely now, filter it narrowly with a comment explaining why.

## Acceptance Criteria

- Normal test output is warning-clean, or remaining warnings are intentionally filtered.
- No broad warning filters hide unrelated future warnings.
- Behavior remains unchanged.

## Verification

- `make test-static`
- `make test-e2e`
- `scripts/run-all-tests.sh --quick`
