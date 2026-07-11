# P1-07 SEO And Indexing Policy Lock

## Summary

- What changed: Marked the session/current-teacher route `/teacher` as `noindex`, added backend `static/robots.txt` to match the frontend robots policy, expanded sitemap/robots contract tests to cover both backend and frontend static assets, and added rendered metadata assertions for public Open Graph, error-page noindex/statuses, and protected-route noindex pages.
- Why it changed: P1-07 requires public canonical routes to be indexable and present in sitemap, while private/auth/admin/forum/error/token-sensitive routes stay out of sitemap and render `noindex, nofollow` when browser HTML exists.
- Ticket(s): `ticket/P1-07-seo-and-indexing-policy-lock.md`

## Files Touched

- `frontend/src/routes/teacher/+page.svelte`
- `frontend/src/routes/public-pages.e2e.ts`
- `frontend/src/routes/forum/new/page.svelte.e2e.ts`
- `frontend/src/routes/forum/page.svelte.e2e.ts`
- `frontend/src/routes/forum/post/page.svelte.e2e.ts`
- `frontend/src/routes/profile/create/page.svelte.e2e.ts`
- `frontend/src/routes/profile/edit/page.svelte.e2e.ts`
- `frontend/src/routes/teacher/page.svelte.e2e.ts`
- `frontend/src/routes/update-password/page.svelte.e2e.ts`
- `tests/test_static_html_contracts.py`
- `static/robots.txt`
- `docs/route-status-matrix.md`

## Verification

Commands run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=tests/stubs pytest tests/test_static_html_contracts.py -q
npm run test:e2e:public
npm run test:e2e:forum
npx playwright test src/routes/profile/create/page.svelte.e2e.ts src/routes/profile/edit/page.svelte.e2e.ts src/routes/teacher/page.svelte.e2e.ts src/routes/update-password/page.svelte.e2e.ts src/routes/admin/page.svelte.e2e.ts src/routes/validation/page.svelte.e2e.ts --grep "renders the teacher profile creation form|renders prefilled teacher profile edit forms|renders mocked backend profile data|renders the update password form|renders administrator tools|renders the validation workflow"
npx playwright test src/routes/validation/page.svelte.e2e.ts --grep "renders validation"
scripts/run-all-tests.sh --quick
```

Results:

- Passed: static sitemap/robots contracts passed 96 tests; public SEO suite passed 18 tests; forum suite passed 17 tests; targeted protected noindex slice passed 5 tests; validation noindex slice passed 2 tests; quick gate passed Svelte check, frontend lint, and Python static tests.
- Failed: full `npm run test:e2e:auth` had two unrelated `/forgot` failures; full `npm run test:e2e:profile` had two unrelated `/profile/create` failures. The SEO-touched tests inside those suites passed in targeted reruns.
- Not run: full `scripts/run-all-tests.sh`.

## Known Issues

- Forum list/detail/create remain intentionally private/noindex; public indexing needs a dedicated product/moderation decision.
- Dynamic `/teacher/[urlId]` pages are public and canonical, but the current static sitemap does not enumerate data-driven teacher profile URLs.
- Existing full auth/profile Playwright suite failures remain outside this ticket's SEO changes and should be handled separately.

## Next Best Step

- Continue with P1-08 Forum HTML Safety Contract.

## Notes For The Next Agent

- Relevant docs: `docs/route-status-matrix.md`, `ticket/P1-07-seo-and-indexing-policy-lock.md`
- Relevant tests: `frontend/src/routes/public-pages.e2e.ts`, `tests/test_static_html_contracts.py`
- Intentional legacy behavior: sitemap includes only static public canonical URLs; noindex routes are excluded from both `static/sitemap.xml` and `frontend/static/sitemap.xml`.
