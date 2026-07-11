# P1-10 Critical Flow Slow JS Coverage

## Summary

- What changed: Expanded disabled-JavaScript fallback coverage to include update password, profile create, forum detail interactions, and admin actions. Added explicit `<noscript>` warnings to JavaScript-required admin tools and forum post interactions so users are not left with silent client-only forms when hydration is unavailable. Fixed the legacy pytest E2E uvicorn fixture to log to a temp file instead of an undrained pipe, preventing public-page navigation timeouts during the full gate.
- Why it changed: P1-10 requires critical flows to either keep users on Svelte-owned fallback paths or clearly identify JavaScript-required interactions without exposing raw backend JSON or silent data loss.
- Ticket(s): `ticket/P1-10-critical-flow-slow-js-coverage.md`

## Files Touched

- `frontend/src/routes/form-fallbacks.e2e.ts`
- `frontend/src/routes/admin/+page.svelte`
- `frontend/src/routes/forum/post/+page.svelte`
- `tests/e2e/test_public_pages_playwright.py`

## Verification

Commands run:

```bash
npx playwright test src/routes/form-fallbacks.e2e.ts
make test-static
scripts/run-all-tests.sh --quick
make PYTEST_E2E_WORKERS=1 test-e2e
scripts/run-all-tests.sh
```

Results:

- Passed: disabled-JavaScript fallback suite passed 9 tests; Python static tests passed 161 tests; quick gate passed Svelte check, frontend lint, and Python static tests; focused legacy pytest E2E passed 38 tests.
- Passed: full `scripts/run-all-tests.sh` completed successfully with all status files at `0`: frontend Playwright passed 96 tests, frontend integration passed 14 tests, Python static passed 161 tests, and legacy pytest E2E passed 38 tests.

## Known Issues

- Full frontend auth/profile suite failures observed during P1-07 did not reproduce in the canonical full gate.

## Next Best Step

- Proceed to P2-11 Normalize API Client Usage.

## Notes For The Next Agent

- Relevant docs: `docs/form-fallback-matrix.md`, `ticket/P1-10-critical-flow-slow-js-coverage.md`
- Relevant tests: `frontend/src/routes/form-fallbacks.e2e.ts`
- Intentional behavior: forum post vote/comment/edit and admin report/delete remain JavaScript-required, but now render no-JS recovery copy instead of silently presenting client-only actions.
- The legacy pytest E2E fixture now writes uvicorn output to a temp log file and removes it during teardown; this avoids server stalls caused by a full `stdout=PIPE` during longer runs.
