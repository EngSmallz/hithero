# B2 profile simple mutations

## Summary

- Extended `ProfileRepository` and `ProfileMutationService` for teacher-name
  and wishlist updates.
- Preserved the wishlist affiliate suffix
  `&tag=h0mer00mher0-20`, existing success payloads, permission checks, and
  route paths.
- Reused repository-owned transaction cleanup established by the school-update
  slice; no production schema or legacy route changed.

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

- Focused profile/directory/contract tests: 17 passed.
- Backend static suite: 181 passed.
- Canonical full parallel gate passed at
  `.tmp/test-logs/20260711-010628/`: Python static 181, frontend Playwright
  97, frontend integration 16, and legacy pytest E2E 38.

## Known issues

- URL-ID allocation/update, image upload, registration, login, and password
  workflows remain for later B2/B3 slices.
- No migration, job, observability, or legacy browser-route work was included.

## Next best step

- Extract URL-ID validation/allocation with explicit collision tests, then
  address the upload/provider boundary separately.
