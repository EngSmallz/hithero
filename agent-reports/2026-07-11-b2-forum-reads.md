# B2 forum read boundary slice

## Summary

- Moved forum post, single-post, and comment-list queries into
  `ForumRepository`.
- Added `ForumService` read orchestration and centralized record sanitization/
  serialization for forum responses.
- Preserved existing ordering, not-found details, sanitized output, and 500
  response behavior; removed the router's unused direct session helpers.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_forum_service.py tests/test_forum_formatting.py \
  tests/test_forum_session_cleanup.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused forum service/API/session-cleanup tests: 20 passed.
- Backend static suite: 225 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Forum authorization policy is still represented by service inputs and legacy
  role strings; B3 will centralize policy/error mapping.
- Validation/moderation/admin router workflows remain for the next B2 slice.

## Next Best Step

- Extract validation list/actions and district-scope policy, then update the
  B2 completion plan before beginning B3 normalization.
