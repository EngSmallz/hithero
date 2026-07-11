# B5 one-shot job runner slice

## Summary

- Added `backend.jobs.runner` with observable success/failure results and
  `backend.jobs.cli` one-shot entry points for daily, Tuesday, Wednesday, and
  Thursday jobs.
- Replaced daemon-thread internal triggers with synchronous compatibility calls
  to the same runner; scheduler invocations now run to completion and expose
  exit status/logging through the CLI.
- Documented the scheduler/worker execution model while preserving existing
  internal route paths and response payloads.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_job_runner.py tests/test_backend_baseline_contracts.py \
  tests/test_app_factory.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused job/route/factory tests: 5 passed.
- Backend static suite: 240 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.

## Known Issues

- Job functions still live in `app.py` and lack durable idempotency keys,
  cross-process locking, persisted run records, and provider timeout/retry
  policies.
- Internal compatibility triggers still execute in the web process; production
  scheduling should use the documented one-shot CLI until a dedicated worker
  deployment is configured.

## Next Best Step

- Move job use cases/integrations out of `app.py`, add idempotency/locking and
  provider adapters, then add production-shaped migration scaffolding.
