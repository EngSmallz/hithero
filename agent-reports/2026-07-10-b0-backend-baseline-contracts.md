# B0 backend baseline contracts — 2026-07-10

## Summary

Established the B0 compatibility baseline for the backend modernization. Added
an exact business API/action route snapshot test and a route inventory covering
callers, current authentication behavior, legacy ownership, existing test
coverage, and production evidence gaps. Updated the backend completion plan to
mark B0 complete and B1 next.

## Why

`app.py` currently owns composition, persistence setup, models, jobs,
integrations, and endpoints. Before extracting any boundary, the route surface
and current behavior need an explicit review artifact that can detect accidental
method/path changes.

## Files changed

- `tests/test_backend_baseline_contracts.py` — exact route/method contract
  snapshot for the business API/action surface.
- `docs/backend-baseline-contracts.md` — inventory, baseline evidence, and
  production assumptions that remain unverified.
- `docs/backend-completion-plan.md` — B0 status and links to the evidence.

## Verification

Command:

```text
PATH=/opt/miniconda3/bin:$PATH scripts/run-all-tests.sh
```

Result: passed.

- Python static: 164 passed
- Frontend Playwright: 97 passed
- Frontend integration: 16 passed
- Legacy pytest E2E: 38 passed
- Baseline logs: `.tmp/test-logs/20260710-212030/`

Post-change canonical verification also passed:

- Command: `PATH=/opt/miniconda3/bin:$PATH scripts/run-all-tests.sh`
- Python static: 165 passed
- Frontend Playwright: 97 passed
- Frontend integration: 16 passed
- Legacy pytest E2E: 38 passed
- Logs: `.tmp/test-logs/20260710-213911/`

The first post-change gate at `.tmp/test-logs/20260710-213111/` had one
transient `/forum/post` mobile-navigation timeout (96/97 Playwright tests
passed; all other suites passed). The required focused rerun passed:

```text
npm --prefix frontend run test:e2e -- \
  src/routes/forum/post/page.svelte.e2e.ts -g "opens mobile navigation"
```

It passed 1 test in 29.4 seconds, and the subsequent full gate passed.

Focused B0 contract check should be run as:

```text
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /opt/miniconda3/bin/pytest tests/test_backend_baseline_contracts.py -q
```

## Caveats

The inventory records, but does not resolve, production SQL Server/schema/data
volume details, reverse-proxy behavior, or the scheduler's external trigger
source. Those require operator/staging evidence before B4, B5, or B7 changes.
No production schema or legacy route was altered.

## Next step

Implement the first B1 slice: extract settings/database/session construction
and application wiring behind `backend/main.py`, preserve `app.py` as the
compatibility ASGI export, and keep this route snapshot passing throughout.
