# B2 profile image mutation slice

## Summary

- Moved upload size/MIME validation and permission decision into
  `ProfileMutationService`.
- Moved teacher image persistence into `ProfileRepository` with the shared
  rollback/close transaction convention.
- Preserved validation order, exact error messages, permission response, and
  success payload for `/profile/update_teacher_image/`.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_profile_mutations.py tests/test_profile_read_service.py \
  tests/test_teacher_directory_api.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused profile/directory/route-contract tests: 34 passed.
- Backend static suite: 198 passed in parallel.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- File type detection remains injected from the application composition layer;
  provider/interface normalization is a later B3 task.
- Registration/login/logout, password flows, profile deletion, forum, and
  admin/moderation workflows remain for later slices.

## Next Best Step

- Extract profile deletion and then registration/login/password workflows,
  preserving their current session and response contracts.
