# B2 validation promotion slice

## Summary

- Extended `AdminRepository` and `AdminService` for pending-user validation.
- Moved district-scope comparison, atomic promotion to `registered_users`,
  pending-user deletion, rollback, and session cleanup out of the router.
- Preserved role checks, exact not-found/scope errors, success payload, and
  post-commit validation-email invocation.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_admin_mutations.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused admin/route-contract tests: 10 passed.
- Backend static suite: 230 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Report and emailed flags still use direct router persistence and duplicate
  scope checks.
- Provider interfaces, centralized policy, and typed error mapping remain
  B3/B5 work.

## Next Best Step

- Extract district-scoped report/emailed actions, then the teacher report
  workflow, before completing B2 and beginning B3.
