# B2 pending-user deletion slice

## Summary

- Extended `AdminRepository` and `AdminService` for pending-user deletion.
- Moved pending-user lookup, delete transaction, rollback, and session cleanup
  out of `/validation/delete_user/{user_email}`.
- Preserved the admin-role guard, exact success payload, and legacy 404 detail.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_admin_mutations.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused admin/route-contract tests: 7 passed.
- Backend static suite: 227 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Validation, report, emailed, and user-promotion workflows still contain
  direct router persistence and duplicated district-scope policy.
- Centralized role/scope authorization remains B3 work.

## Next Best Step

- Extract validation promotion and district-scoped report/email actions behind
  `AdminService` and repository transactions.
