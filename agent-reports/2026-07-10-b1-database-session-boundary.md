# B1 database/session boundary — 2026-07-10

## Summary

Extracted SQLAlchemy engine/session construction and declarative metadata into
`backend/db` while preserving the compatibility names used by `app.py` and
existing tests. This is a second, independently committed B1 slice; models,
schemas, migrations, repositories, and domain behavior remain in their
current locations for later slices.

## Changes

- Added `backend/db/session.py` with the existing SQL Server/SQLite URL rules,
  SQLite directory handling, engine options, and a `DatabaseResources` bundle.
- Added `backend/db/base.py` as the shared declarative metadata owner.
- Updated `app.py` to consume the extracted resources and re-export
  `SQLALCHEMY_DATABASE_URL`, `engine`, `SessionLocal`, `Base`, and the existing
  database helper functions for compatibility.
- Added a database-resource boundary test.
- Stabilized one existing `/forum/post` mobile-navigation E2E test by waiting
  for its rendered page heading before clicking the hydrated menu. This is a
  test-readiness assertion only; it does not alter frontend or backend runtime
  behavior.

## Safety boundaries

No model class, table name, column, constraint, migration, API route, response
shape, or legacy browser route changed. `Base.metadata.create_all()` remains
called under the same test/non-test condition as before; production schema
management is still a future B4 concern.

## Verification

Focused command:

```text
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /opt/miniconda3/bin/pytest tests/test_database_session_boundary.py \
  tests/test_database_config.py tests/test_app_factory.py \
  tests/test_backend_baseline_contracts.py -q
```

Result: 16 passed.

The first two post-change full gates recorded the same pre-existing browser
readiness race in `frontend/src/routes/forum/post/page.svelte.e2e.ts` (96/97
Playwright tests passed; all other suites passed). The focused test passed
after the readiness assertion, and the required clean full gate then passed:

```text
PATH=/opt/miniconda3/bin:$PATH scripts/run-all-tests.sh
```

- Python static: 167 passed
- Frontend Playwright: 97 passed
- Frontend integration: 16 passed
- Legacy pytest E2E: 38 passed
- Logs: `.tmp/test-logs/20260710-220859/`

## Caveats and next step

`app.py` still defines all ORM models and Pydantic DTOs. The next B1 slice
should move those definitions to `backend/db` and `backend/schemas` with
table/column names unchanged, then prove router imports and the B0 route
snapshot remain stable.
