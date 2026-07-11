# P1-07: Lock SEO, Sitemap, Robots, And Noindex Policy

## Problem

Public pages should be canonical and indexable. Private, authenticated, admin, validation, and forum pages should be excluded from the sitemap and use `noindex` where browser-rendered HTML can exist.

The policy exists in the modernization docs, but the final implementation should be audited and locked with tests.

## Scope

- Audit all public Svelte routes for title, description, canonical URL, and Open Graph metadata.
- Audit private/authenticated routes for `noindex` and sitemap exclusion.
- Decide whether forum list/detail should remain private/noindex or become public/indexable later.
- Ensure `frontend/static/sitemap.xml`, `static/sitemap.xml`, and robots files agree with the final policy.

## Acceptance Criteria

- Public canonical routes are present in sitemap.
- Private/auth/admin/forum routes are absent from sitemap.
- Noindex routes render `<meta name="robots" content="noindex, nofollow">`.
- Error pages return appropriate statuses and use noindex.
- Tests cover the policy.

## Verification

- `frontend/src/routes/public-pages.e2e.ts`
- `tests/test_static_html_contracts.py`
- Manual review of sitemap and robots files.
- `scripts/run-all-tests.sh`
