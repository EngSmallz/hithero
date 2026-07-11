# B2 password reset workflow slice

## Summary

- Extended `ProfilePasswordService` with reset-token creation, validation, and
  password consumption.
- Moved reset-token persistence and atomic password/token updates into
  `ProfileRepository` with rollback and session cleanup.
- Preserved forgot-password generic response/timing behavior and reset route
  400/200 payloads while retaining email rendering/sending in the router.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_profile_password.py tests/test_profile_auth.py \
  tests/test_admin_mutations.py tests/test_profile_mutations.py \
  tests/test_profile_read_service.py tests/test_teacher_directory_api.py \
  tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused auth/admin/profile/directory/route-contract tests: 53 passed.
- Backend static suite: 217 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the reset path.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Reset-token uniqueness/lifecycle constraints remain a B4 database task.
- Email provider abstraction, timeout/retry policy, rate limits, and API error
  normalization remain B3/B5 work.

## Next Best Step

- Complete the remaining B2 forum and validation/moderation repository/service
  extraction, then start B3 security/API normalization.
