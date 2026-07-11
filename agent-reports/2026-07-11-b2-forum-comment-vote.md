# B2 forum comment and vote slices

## Summary

- Extended `ForumRepository` and `ForumService` for comment creation and vote
  transactions.
- Moved post/parent existence checks, comment-count updates, vote toggling,
  vote-count updates, and rollback/close behavior out of the router.
- Preserved authentication checks, sanitization, exact 400/404/500 details,
  and the existing counter semantics.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_forum_service.py tests/test_forum_formatting.py \
  tests/test_forum_session_cleanup.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused forum service/API/session-cleanup tests: 17 passed.
- Backend static suite: 222 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.
- Browser, integration, and legacy E2E suites were not run for this
  backend-only extraction slice.

## Known Issues

- Forum reads, edit/delete authorization, and comment deletion still remain in
  the router.
- A shared authorization policy and typed central error mapping remain B3 work.

## Next Best Step

- Extract forum edit/delete policies and persistence, then complete validation
  and moderation/admin workflows before beginning B3 normalization.
