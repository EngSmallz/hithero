# P2-15: Final Dead Code Removal Pass

## Problem

After migrated routes, redirects, SEO, and tests are stable, the repo should remove static HTML/JS that is no longer needed. This should happen only after replacement behavior is proven.

## Scope

- Identify static pages and scripts no longer used by migrated routes.
- Remove dead files only when redirects and tests prove they are obsolete.
- Keep intentionally retained legacy files with documented reasons.
- Avoid broad cleanup before P1 legacy route decisions are complete.

## Acceptance Criteria

- No migrated Svelte route depends on legacy page scripts.
- Removed files have replacement routes and redirect coverage.
- Retained legacy files have documented reasons.
- Full verification remains green after removal.

## Verification

- `rg '/pages/|pages/.*\\.html|static/js' frontend backend tests docs`
- `tests/test_static_html_contracts.py`
- `tests/test_clean_routes.py`
- `scripts/run-all-tests.sh`
