# B3 typed domain-error boundary slice

## Summary

- Added `DomainError` subclasses and a central FastAPI exception handler with
  stable `{detail: ...}` JSON mapping for 400/403/404/409 errors.
- Converted profile password/URL/image and admin policy errors to typed domain
  errors while preserving existing router mappings during the incremental
  migration.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_csrf.py tests/test_auth_core.py tests/test_app_factory.py \
  tests/test_profile_auth.py tests/test_profile_password.py \
  tests/test_admin_mutations.py tests/test_forum_service.py \
  tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused B3/auth/domain/route-contract tests: 43 passed, with 3 existing UTC
  datetime deprecation warnings.
- Backend static suite: 237 passed in parallel, with the same 3 warnings.

## Known Issues

- Broad router exception handlers remain in legacy and unconverted endpoint
  paths; the typed mapping is an incremental foundation, not a completed B3
  audit.
- Explicit response DTO coverage, rate-limit shared storage, authorization
  negatives, and provider interfaces remain.

## Next Best Step

- Convert forum/admin/profile router catches to typed mappings where
  compatibility tests permit, then add explicit response models and security
  negative coverage.
