# Test Workflow

The canonical full verification command is:

```bash
scripts/run-all-tests.sh
```

Use it before declaring modernization work complete.

## Quick Feedback

```bash
scripts/run-all-tests.sh --quick
```

This runs frontend check/lint plus Python static tests. It skips formatting and browser suites.

## Full Gate Behavior

The script runs frontend format/check/lint first. When both frontend Playwright and frontend integration suites are selected, it builds the frontend once and sets `PLAYWRIGHT_SKIP_BUILD=1` so the Playwright suite can preview the already-built output.

Then it runs slow suites in parallel:

- Python static tests
- Frontend Playwright E2E
- Frontend real-stack integration tests
- Legacy pytest E2E

Parallel browser testing is intentional. The backend should tolerate concurrent users and requests. If flakes appear, investigate fixture collisions, shared generated frontend state, port allocation, database setup, and backend session handling.

Inside the already-parallel full gate, the legacy pytest browser smoke suite defaults to one internal pytest worker to avoid nested browser-server teardown hangs. Override `PYTEST_E2E_WORKERS` when you intentionally want to stress that legacy suite with more internal workers; the Svelte Playwright and real-stack integration suites remain parallel by default.

## Logs

Parallel suite logs are written to:

```text
.tmp/test-logs/<timestamp>/
```

The script prints a concise summary with each suite's status, duration, and log path. On failure it prints the tail of the failing suite log.

## Focused Backend Commands

```bash
make test-static
make test-static-db
make test-e2e
make test-forum-api
make test-teachers-api
```

## Focused Frontend Commands

```bash
npm --prefix frontend run check
npm --prefix frontend run lint
npm --prefix frontend run test:e2e
npm --prefix frontend run test:e2e:forum
npm --prefix frontend run test:e2e:auth
npm --prefix frontend run test:e2e:profile
npm --prefix frontend run test:e2e:public
npm --prefix frontend run test:integration
npm --prefix frontend run test:integration:one
```

Use focused commands while iterating. Use the full gate for release confidence.
