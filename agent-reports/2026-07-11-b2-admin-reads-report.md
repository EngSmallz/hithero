# B2 admin read/report boundary slice

## Summary

- Moved validation-list queries and teacher report data assembly into
  `AdminRepository` and `AdminService`.
- Preserved teacher district filtering, current-teacher session hydration,
  response serialization, report formatting, no-teacher behavior, and the
  existing temporary-file/email handoff.
- Routers now retain HTTP mapping and provider/file orchestration rather than
  SQLAlchemy query construction.

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

- Admin provider calls and temporary report-file lifecycle remain in the
  router; durable integration/job handling is B5 work.
- Security policy and broad error normalization remain B3 work.

## Next Best Step

- Record B2 completion status and begin B3 API/security normalization, starting
  with typed domain errors, response contracts, CSRF/session policy, and
  rate-limit isolation.
