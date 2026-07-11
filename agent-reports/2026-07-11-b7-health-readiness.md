# B7 health and readiness probe slice

## Summary

- Added `GET /healthz` for process liveness.
- Added `GET /readyz` with a configured database `SELECT 1` readiness probe and
  a non-sensitive 503 response on dependency failure.
- Updated deployment topology documentation and recorded B2 completion/B3
  progress in the backend completion plan.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_app_factory.py tests/test_csrf.py \
  tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused health/CSRF/factory/route-contract tests: 7 passed.
- Backend static suite: 238 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.

## Known Issues

- Structured request logging, correlation IDs, metrics, exception reporting,
  and production-like staging verification remain B7 work.
- The full parallel release gate has not yet been rerun after the B2/B3/B7
  changes.

## Next Best Step

- Continue B3 rate-limit/provider/security normalization, then add durable job
  execution and operational observability before the final gate.
