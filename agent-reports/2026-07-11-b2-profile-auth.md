# B2 profile registration and login slice

## Summary

- Added `ProfileAuthService` for registration duplicate/queue/password-match
  policy and password-hash authentication.
- Moved registered/pending-user queries and pending-user insertion into
  `ProfileRepository` with rollback and session cleanup.
- Preserved reCAPTCHA handling, legacy session keys, login payloads, and exact
  registration messages.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_profile_auth.py tests/test_admin_mutations.py \
  tests/test_profile_mutations.py tests/test_profile_read_service.py \
  tests/test_teacher_directory_api.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused auth/admin/profile/directory/route-contract tests: 45 passed.
- Backend static suite: 209 passed in parallel.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Session fixation prevention, cookie/CSRF policy, rate-limit shared storage,
  and normalized auth errors remain B3 work.
- Password update/reset and forgot-password provider workflows remain in the
  profile router.

## Next Best Step

- Extract password update/reset and forgot-password persistence/provider
  orchestration, then continue forum and moderation/admin workflows.
