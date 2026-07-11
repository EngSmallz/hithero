# B2 forum deletion workflow slice

## Summary

- Extended `ForumRepository` and `ForumService` for post and comment deletion.
- Moved admin-only post deletion, author/admin comment policy, comment-count
  maintenance, commit, rollback, and session cleanup out of the router.
- Preserved exact 204, 404, 403, and 500 response behavior and deletion
  messages.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_forum_service.py tests/test_forum_formatting.py \
  tests/test_forum_session_cleanup.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused forum service/API/session-cleanup tests: 18 passed.
- Backend static suite: 224 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Forum read queries remain in the router.
- Shared authorization policy and typed central error mapping remain B3 work.

## Next Best Step

- Extract forum read/query serialization, then complete validation/moderation
  repository and district-scope policy boundaries.
