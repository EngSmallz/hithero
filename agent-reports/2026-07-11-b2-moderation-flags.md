# B2 moderation flag workflow slice

## Summary

- Extended `AdminRepository` and `AdminService` with one district-scope-aware
  path for pending-user `report` and `emailed` flags.
- Moved pending-user/teacher scope queries, flag updates, commit, rollback, and
  session cleanup out of the admin router.
- Preserved role gates, success payloads, and the legacy broad 500 mapping for
  scope failures pending B3 error normalization.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_admin_mutations.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused admin/route-contract tests: 11 passed.
- Backend static suite: 231 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Teacher report generation and validation-list reads still use direct router
  queries.
- Role/scope policy and broad error normalization remain B3 work.

## Next Best Step

- Extract validation-list/report generation, then update the B2 completion plan
  and begin B3 security/API boundary normalization.
