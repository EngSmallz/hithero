# P1-06: Complete Legacy Route Cleanup Plan

## Problem

The frontend migration is substantially complete, but legacy `/pages/*.html` serving still exists for deferred or session-sensitive pages. The modernization cannot be considered complete until every legacy page has a final disposition.

## Scope

Create and implement a route-by-route decision for every legacy page:

- Redirect now.
- Keep temporarily with reason.
- Remove after specific replacement proof.

Include both public and authenticated/session-dependent routes.

## Acceptance Criteria

- Every `/pages/*.html` route is classified.
- Redirect-ready public pages redirect to clean canonical URLs for GET and HEAD.
- Deferred pages have documented reasons.
- Sitemap uses only clean canonical public URLs.
- Tests prove redirect and direct-serve behavior for every class.
- Stale static HTML is removed only after replacement and redirect tests are in place.

## Verification

- `tests/test_clean_routes.py`
- `tests/test_static_html_contracts.py`
- `tests/e2e/test_public_pages_playwright.py`
- `scripts/run-all-tests.sh`
