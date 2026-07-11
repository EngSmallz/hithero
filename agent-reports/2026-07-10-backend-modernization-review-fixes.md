# Backend modernization review fixes

## What changed

- Enforced district scope when teachers mark pending users reported or emailed.
- Replaced the shared teacher report filename with a request-unique temporary file and guaranteed cleanup.
- Preserved the `Secure` attribute when the Svelte login action copies the backend session cookie in HTTPS deployments.
- Closed database sessions on legacy teacher and teacher URL lookup routes, and avoided opening a session before administrative deletion authorization succeeds.
- Preserved intentional 403/404 responses instead of converting them to 500s.
- Preserved query strings across legacy public-page redirects.
- Added focused backend regression coverage and stabilized the admin dependent-select Playwright test by waiting for initial page synchronization.

## Verification

- Focused backend tests: `28 passed in 10.49s`.
- Focused admin Playwright rerun: `1 passed`.
- Canonical `scripts/run-all-tests.sh` through the elevated interactive login shell: all selected checks passed.
  - Python static tests: passed.
  - Frontend Playwright tests: passed.
  - Frontend integration tests: passed.
  - Legacy pytest E2E tests: passed.

## Caveats and next step

- The non-interactive shell does not expose `npm`; the canonical gate must currently be invoked through the user's interactive login shell. That shell also prints a harmless missing `/opt/homebrew/bin/brew` warning from `.zprofile`.
- No known issue remains from the reviewed findings. The next step is review and commit of the scoped changes.
