# P1-06 Legacy Route Cleanup Plan

## Summary

- What changed: Added an explicit legacy page disposition table to `docs/route-status-matrix.md`, moved `/pages/wishlist_setup.html` into the redirect-ready public legacy class, and added an exhaustive backend test proving every `pages/*.html` file is classified.
- Why it changed: P1-06 requires every legacy static page to have a final cleanup decision, redirect-ready public pages to redirect on GET and HEAD, deferred pages to carry documented reasons, and tests to prove each serving class.
- Ticket(s): `ticket/P1-06-legacy-route-cleanup-plan.md`

## Files Touched

- `backend/routers/legacy.py`
- `docs/route-status-matrix.md`
- `tests/test_clean_routes.py`
- `tests/e2e/test_public_pages_playwright.py`

## Verification

Commands run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=tests/stubs pytest tests/test_clean_routes.py tests/test_static_html_contracts.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=tests/stubs pytest tests/e2e/test_public_pages_playwright.py -q
make test-static
scripts/run-all-tests.sh --quick
```

Results:

- Passed: `tests/test_clean_routes.py` and `tests/test_static_html_contracts.py` together passed 98 tests; `make test-static` passed 153 tests; `scripts/run-all-tests.sh --quick` passed Svelte check, frontend lint, and Python static tests.
- Skipped: `tests/e2e/test_public_pages_playwright.py` collected 26 tests but skipped because `playwright.sync_api` is unavailable in this Python environment.
- Failed: none.
- Not run: full `scripts/run-all-tests.sh`.

## Known Issues

- Deferred legacy pages remain intentionally direct-served until their route-specific removal proof is complete.
- Backend tests still emit existing SQLAlchemy and Pydantic deprecation warnings.

## Next Best Step

- Continue with P1-07 SEO and indexing policy lock, then run the full canonical gate before claiming the P1 set is complete.

## Notes For The Next Agent

- Relevant docs: `docs/route-status-matrix.md`, `ticket/P1-06-legacy-route-cleanup-plan.md`
- Relevant tests: `tests/test_clean_routes.py`, `tests/test_static_html_contracts.py`, `tests/e2e/test_public_pages_playwright.py`
- Intentional legacy behavior: reset/update password, forum, teacher, profile, validation, and admin legacy HTML files remain direct-served for token-, auth-, query-, or role-sensitive fallback reasons documented in the route matrix.
