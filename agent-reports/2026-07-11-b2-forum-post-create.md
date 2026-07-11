# B2 forum post creation slice

## Summary

- Added `ForumRepository` and `ForumService` for post creation.
- Moved sanitized post construction, persistence, commit, refresh, rollback,
  and session cleanup out of the forum router.
- Preserved authentication behavior, sanitizer boundary, response serialization,
  rate-limit decorator, and 500 response contract.
- Hardened focused auth API tests against shared test-only limiter state so
  combined backend checks do not create false 429 failures.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_forum_service.py tests/test_forum_formatting.py \
  tests/test_forum_session_cleanup.py tests/test_profile_password.py \
  tests/test_profile_auth.py tests/test_admin_mutations.py \
  tests/test_profile_mutations.py tests/test_profile_read_service.py \
  tests/test_teacher_directory_api.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused forum/auth/admin/profile/directory/route-contract tests: 67 passed,
  with 3 existing UTC datetime deprecation warnings.
- Backend static suite: 219 passed in parallel, with the same 3 warnings.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Forum comment, vote, read, edit, and delete workflows still use direct
  router persistence and need explicit service/policy boundaries.
- Centralized forum authorization/error mapping remains B3 work.

## Next Best Step

- Extract forum comment creation and vote transaction workflows, then move
  forum edit/delete authorization into a shared policy service.
