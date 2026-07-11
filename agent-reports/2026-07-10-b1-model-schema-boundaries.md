# B1 model/schema boundaries — 2026-07-10

## Status

Implemented and ready as a focused B1 milestone. The browser-inclusive full
gate is still pending; the faster backend/static boundary checks below are not
being represented as full-gate evidence.

## Changes

- Moved all SQLAlchemy model classes from `app.py` to
  `backend/db/models.py` without changing table names, columns, foreign keys,
  or constraints.
- Moved forum and teacher Pydantic DTOs to `backend/schemas/forum.py` and
  `backend/schemas/teachers.py`.
- Kept `app.py` module-level imports for all former model/schema names so
  existing tests, integration helpers, and router registration remain
  compatible.
- Added boundary tests proving the new modules and legacy table names.

## Verification completed

Focused backend compatibility command:

```text
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /opt/miniconda3/bin/pytest tests/test_database_config.py \
  tests/test_database_session_boundary.py tests/test_app_factory.py \
  tests/test_backend_baseline_contracts.py tests/test_teacher_directory_api.py \
  tests/test_forum_formatting.py tests/test_forum_session_cleanup.py -q
```

Result: 37 passed. Model/schema boundary check: 5 passed. The focused
factory/database/route/config/model-schema set passed 18 tests, and the full
backend static suite passed 169 tests in 28.31 seconds.

The safe quick gate passed with the explicit Conda runtime:

```text
PATH=/opt/miniconda3/bin:$PATH scripts/run-all-tests.sh --quick
```

Result: frontend check/lint and Python static tests passed; Python static log:
`.tmp/test-logs/20260710-222433/Python_static_tests.log`.

An initial full-gate attempt after resuming failed before tests because the
shell PATH omitted npm (`npm: command not found`). The correct runtime PATH for
the later full gate is `/opt/miniconda3/bin:/usr/local/bin:$PATH`.

## Pending verification and next step

After the next browser-inclusive verification window, run:

```text
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH scripts/run-all-tests.sh
```

If it passes, append the log directory to this report. Do not alter production
schema or remove `app.py` compatibility imports in that follow-up.
