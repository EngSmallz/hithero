# B2 profile read-only service slice

## Summary

- Added `ProfileRepository` for context-based teacher lookup and user-owned
  teacher lookup.
- Added `ProfileReadService` for public teacher-info serialization, session
  context construction, teacher access policy, and profile URL generation.
- Moved SQL and image encoding out of the four read-only profile endpoints:
  `get_teacher_info`, `myinfo`, `check_access_teacher`, and `teacher_url`.
- Preserved route paths, session keys, response fields, 404/403 behavior, and
  the shared HTML error handling installed by the legacy router.

## Verification

Commands run:

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_profile_read_service.py tests/test_teacher_directory_api.py \
  tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

Results:

- Focused profile/directory/route-contract tests: 14 passed.
- Backend static suite: 178 passed.
- The last accumulated full parallel gate remains green at
  `.tmp/test-logs/20260711-003807/`; browser/integration suites were not
  rerun for this read-only extraction slice.

## Known issues

- Mutation, login, password-reset, upload, and provider workflows remain in
  `backend/routers/profile.py` for later transactional slices.
- No schema, migration, job, or legacy browser-route changes were made.

## Next best step

- Extract profile mutation persistence behind a repository/service boundary,
  starting with one update workflow and an explicit rollback test.
