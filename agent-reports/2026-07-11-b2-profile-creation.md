# B2 profile creation and URL allocation slice

## Summary

- Moved profile create-count checks, affiliate-link construction, URL-ID
  allocation/retry, and profile creation orchestration into
  `ProfileMutationService`.
- Moved teacher insertion and registered-user counter update into one
  repository-owned transaction with rollback and session cleanup.
- Preserved the existing route, response payloads, profile-create guard, URL
  prefix behavior, and affiliate suffix. No schema or legacy route changed.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_profile_mutations.py tests/test_profile_read_service.py \
  tests/test_teacher_directory_api.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused profile/directory/route-contract tests: 30 passed.
- Backend static suite: 194 passed in parallel.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- URL allocation still relies on application-level collision retries until B4
  can add and verify production-safe database uniqueness.
- Image upload, registration/login/logout, password flows, profile deletion,
  forum, and admin/moderation workflows remain for later B2 slices.

## Next Best Step

- Extract profile image validation/persistence or profile deletion, with
  explicit authorization and rollback coverage.
