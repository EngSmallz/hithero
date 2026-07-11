# B2 authenticated password update slice

## Summary

- Added `ProfilePasswordService` for password-match and old-password policy.
- Moved password-hash lookup and transactional update into
  `ProfileRepository`.
- Preserved the authenticated route, status/message payloads, and legacy
  behavior for mismatch, invalid old password, and successful updates.

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

- Focused auth/admin/profile/directory/route-contract tests: 49 passed.
- Backend static suite: 213 passed in parallel.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Forgot-password token creation/reset and email-provider orchestration remain
  in the profile router.
- Password policy normalization, rate limiting, CSRF, and session-fixation
  hardening remain B3 work.

## Next Best Step

- Extract forgot-password/reset-token workflows, then move to forum and
  validation/moderation service boundaries.
