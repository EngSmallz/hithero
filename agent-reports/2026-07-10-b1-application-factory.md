# B1 application factory — 2026-07-10

## Summary

Introduced the first B1 package-boundary slice without changing the public
route surface or production schema. `backend/main.py` now owns construction of
the FastAPI application shell, while `backend/core/settings.py` owns the
application-environment settings required by that shell. `app.py` remains the
compatibility ASGI entry point and continues to register the existing routers,
models, jobs, and endpoints.

## Changes

- Added `BackendSettings` with the existing CORS and session-cookie behavior.
- Added `create_app(settings)` for FastAPI, SessionMiddleware, CORS, limiter,
  documentation disabling, and `/static` mounting.
- Kept the optional slowapi fallback behavior.
- Updated `app.py` to create the application through the factory and preserve
  the existing `APP_ENV`, settings helpers, and `limiter` compatibility names.
- Added a focused factory wiring test and retained the B0 route snapshot.

## Safety boundaries

This slice does not move ORM models, database engine/session construction,
domain logic, routers, jobs, integrations, or legacy browser routes. It does
not call `create_all()` differently and does not alter a production table or
column. The next B1 slice should extract database/session construction behind
the same compatibility entry point.

## Verification

Focused command:

```text
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /opt/miniconda3/bin/pytest tests/test_app_factory.py \
  tests/test_backend_baseline_contracts.py tests/test_database_config.py -q
```

Result: 15 passed.

Full post-change gate:

```text
PATH=/opt/miniconda3/bin:$PATH scripts/run-all-tests.sh
```

Result: passed.

- Python static: 165 passed
- Frontend Playwright: 97 passed
- Frontend integration: 16 passed
- Legacy pytest E2E: 38 passed
- Logs: `.tmp/test-logs/20260710-215043/`

## Caveats and next step

`app.py` is still a large composition/implementation module. This report is
not a claim that B1 is complete. Continue with database/session extraction,
then model/schema boundaries, while preserving `app.py` until deployment and
tests use the new application entry point.
