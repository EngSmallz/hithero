# B2 admin account deletion slice

## Summary

- Added `AdminRepository` and `AdminService` for administrator account
  deletion.
- Moved registered-user lookup, teacher cleanup, commit, rollback, and session
  close out of the admin router.
- Preserved the admin-role and secret checks, not-found status/detail, success
  payload, and associated teacher deletion behavior.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_admin_mutations.py tests/test_profile_mutations.py \
  tests/test_profile_read_service.py tests/test_teacher_directory_api.py \
  tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused admin/profile/directory/route-contract tests: 38 passed.
- Backend static suite: 202 passed in parallel.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Other validation and report workflows still use direct router persistence and
  scope checks; those remain for the forum/admin B2 slices.
- Admin secret handling and centralized authorization normalization remain B3
  work.

## Next Best Step

- Extract registration/login/logout and password workflows, then continue with
  forum and validation/admin service boundaries.
