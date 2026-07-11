# B4 migration scaffold slice

## Summary

- Added Alembic configuration, environment wiring, script template, and a
  reviewed-baseline revision under `migrations/`.
- Production startup now skips implicit `Base.metadata.create_all()`; local
  environments retain explicit convenience initialization.
- Added migration runbook requirements for SQL Server schema capture,
  backup/restore rehearsal, baseline stamping, and production-dialect review.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_migration_policy.py tests/test_database_config.py \
  tests/test_public_pages.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused migration/config/route-contract tests: 30 passed.
- Backend static suite: 242 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.

## Known Issues

- The baseline revision is intentionally a no-op until production SQL Server
  schema evidence is supplied and reviewed; no production constraints were
  inferred or added.
- Alembic execution and SQL Server rehearsal remain release/staging work.

## Next Best Step

- Add B4 data-integrity constraint/index review artifacts, then run the first
  meaningful full gate before claiming release readiness.
