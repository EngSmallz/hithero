# B2 profile school mutation slice

## Summary

- Added `ProfileMutationService.update_teacher_school` and moved its SQL
  update into `ProfileRepository`.
- Repository persistence now owns commit, rollback on failure, and session
  close for this mutation.
- Preserved the existing permission check, success payload, route path, and
  broad HTTP error mapping in `backend/routers/profile.py`.
- No schema or migration change was made.

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

- Focused profile/directory/contract tests: 16 passed.
- Backend static suite: 180 passed.
- The last accumulated full parallel gate remains green at
  `.tmp/test-logs/20260711-003807/`; browser/integration suites were not
  rerun for this isolated mutation slice.

## Known issues

- Other profile mutations, authentication, password reset, and uploads remain
  in the router and still need individually tested service boundaries.
- No production schema, legacy route, or job behavior changed.

## Next best step

- Extract the next small profile mutation, preferably teacher name or wishlist,
  while preserving its current status/error behavior.
