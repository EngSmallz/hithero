# B3 CSRF and session-fixation boundary slice

## Summary

- Added origin/referer validation middleware for unsafe mutations under
  profile, forum, validation, admin, and contact API paths.
- Added explicit local/test bypass so existing test and local development
  behavior remains usable; deployed environments require a configured
  same-origin request source.
- Added `establish_user_session`, which clears pre-auth session state before
  storing authenticated identity keys at login.

## Verification

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_csrf.py tests/test_auth_core.py tests/test_app_factory.py \
  tests/test_profile_auth.py tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

- Focused CSRF/auth/factory/route-contract tests: 16 passed.
- Backend static suite: 236 passed in parallel, with 3 existing UTC datetime
  deprecation warnings in the password reset path.
- Browser, integration, and legacy E2E suites were not run for this focused
  backend security boundary slice.

## Known Issues

- The CSRF boundary is origin-based and does not yet expose a form token for
  non-browser clients; production proxy/origin configuration still needs
  staging verification.
- Typed central domain errors, explicit response models, rate-limit shared
  storage, and provider timeouts remain B3/B5 work.

## Next Best Step

- Add central typed error mapping and explicit API DTOs, then audit rate-limit
  keys/storage and authorization negatives endpoint by endpoint.
