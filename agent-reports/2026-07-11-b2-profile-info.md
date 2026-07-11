# B2 final profile mutation boundary slice

## Summary

- Moved the remaining `update_info` SQL write into
  `ProfileRepository.update_teacher_about_me` and
  `ProfileMutationService`.
- Verified that profile, forum, and admin routers no longer contain direct
  SQLAlchemy queries or transaction calls.
- Preserved the existing payload and legacy permission/error behavior.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_profile_mutations.py tests/test_profile_auth.py \
  tests/test_profile_password.py tests/test_admin_mutations.py \
  tests/test_forum_service.py tests/test_forum_formatting.py \
  tests/test_forum_session_cleanup.py tests/test_teacher_directory_api.py \
  tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused B2 domain/route-contract tests: 78 passed, with 3 existing UTC
  datetime deprecation warnings.
- Backend static suite: 232 passed in parallel, with the same 3 warnings.
- Router SQL scan: no direct `db.query/execute/add/delete/commit/rollback` or
  `session_factory()` calls remain in profile, forum, or admin routers.

## Known Issues

- B3 security/API normalization, B4 migrations/constraints, B5 durable jobs,
  B6 legacy retirement, and B7 operational proof remain outstanding.

## Next Best Step

- Update the completion plan with B2 evidence and begin B3 with typed domain
  errors, explicit response contracts, and session/CSRF policy.
