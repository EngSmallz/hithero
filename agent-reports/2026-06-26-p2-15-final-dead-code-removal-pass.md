# P2-15 Final Dead Code Removal Pass

## Summary

- What changed: Removed the unused `static/common-scripts.js` file after confirming no source, test, backend, frontend, or docs references remain.
- Why it changed: P2-15 calls for removing static HTML/JS only when it is demonstrably unused, while keeping intentionally retained legacy assets documented.
- Ticket(s): `ticket/P2-15-final-dead-code-removal-pass.md`

## Files Touched

- `static/common-scripts.js`

## Implementation Notes

- No legacy HTML files were removed in this pass. Even redirect-ready public HTML files are still used by backend clean-route aliases and the legacy pytest E2E suite.
- Retained legacy HTML disposition remains documented in `docs/route-status-matrix.md`.
- Retained `static/js/*` files are still referenced by retained legacy pages and static HTML contract tests.

## Verification

Commands run:

```bash
rg '/pages/|pages/.*\.html|static/js' frontend backend tests docs
PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 APP_ENV=test SECRET_KEY=test-secret pytest tests/test_static_html_contracts.py tests/test_clean_routes.py -q
rg -n "common-scripts\.js" . -g '*.*'
scripts/run-all-tests.sh
```

Results:

- Passed: inventory search confirmed remaining `/pages/` and `static/js` references are intentional legacy router/docs/tests/static-contract references.
- Passed: focused static HTML and clean-route tests passed 102 tests.
- Passed: `common-scripts.js` search found no remaining references.
- Passed: full canonical gate passed all selected checks: Python static, frontend Playwright, frontend integration, and legacy pytest E2E.

## Known Issues

- Legacy HTML remains by design. Removing those files requires a future backend alias strategy change so `make test-e2e` and clean-route contracts no longer depend on serving `pages/*.html` directly.

## Next Best Step

- All listed modernization tickets through P2-15 are complete. Next work should shift to review, staging/deployment validation, or intentionally opening a new ticket for backend legacy alias retirement.
