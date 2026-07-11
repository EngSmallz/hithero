# B2 profile URL-ID mutation slice

## Summary

- Moved URL-ID format validation and collision policy out of
  `backend/routers/profile.py` into `ProfileMutationService`.
- Added repository-owned URL-ID lookup and transactional update with rollback
  and session cleanup.
- Preserved the existing route, permission check, success payload, and 400,
  409, and 500 response behavior. No schema or legacy route changed.

## Files Touched

- `backend/services/profile_mutations.py`
- `backend/repositories/profile.py`
- `backend/routers/profile.py`
- `tests/test_profile_mutations.py`

## Verification

Commands run:

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_profile_mutations.py tests/test_profile_read_service.py \
  tests/test_teacher_directory_api.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

Results:

- Focused profile/directory/route-contract tests: 25 passed.
- Backend static suite: 189 passed in parallel.
- Browser, integration, and legacy E2E suites were not run because this was a
  backend-only extraction with API contract coverage.

## Known Issues

- URL-ID collision detection and update remain two repository transactions;
  database-level uniqueness is deferred to B4 after production data review.
- Profile creation, image upload, registration, login, password, forum, and
  admin/moderation workflows remain for later slices.

## Next Best Step

- Extract profile creation and URL-ID allocation as the next transactional
  identity/profile slice, including collision retry and rollback coverage.

## Notes For The Next Agent

- Relevant plan: `docs/backend-completion-plan.md`, B2 identity/profile.
- Relevant tests: `tests/test_profile_mutations.py`.
- Preserve the legacy URL-ID pattern and exact error messages until a reviewed
  compatibility change is approved.
