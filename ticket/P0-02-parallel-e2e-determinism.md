# P0-02: Make Parallel E2E/Integration Execution First-Class And Deterministic

## Problem

The project intentionally parallelizes E2E suites. That should remain true: the backend must tolerate parallel browser sessions and concurrent requests, as any website backend should.

The issue to fix is not parallelism itself. The issue is collisions between test fixtures, generated frontend tooling state, ports, and shared records.

## Scope

- Preserve parallel E2E and integration execution.
- Make tests use unique users, emails, posts, teachers, and other mutable records per test or per worker.
- Avoid mid-suite database resets that can affect another worker.
- Prevent multiple frontend dev/build processes from racing over shared `.svelte-kit` or build output.
- Keep the suite stressing real backend concurrency.

## Acceptance Criteria

- `scripts/run-all-tests.sh` passes repeatedly with parallel slow suites enabled.
- E2E/integration tests can run with multiple workers against the same backend without cross-test data contamination.
- No flakes from shared users, shared posts, shared teacher rows, stale auth, `database is locked`, or generated SvelteKit file races.
- The solution does not serialize all E2E work merely to hide concurrency issues.
- Any intentionally serialized setup step is documented and occurs before the parallel browser work.

## Verification

- Run `scripts/run-all-tests.sh` repeatedly from a clean checkout.
- Run frontend integration tests with the default worker count.
- Run frontend Playwright E2E with the default worker count.
- Confirm failures, if any, are real app failures rather than fixture/tooling races.
