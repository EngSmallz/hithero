# P2-11 Normalize API Client Usage

## Summary

- What changed: Expanded `apiFetch` error extraction to use both `detail` and `message`, then moved repeated browser-side API calls in forum, admin, validation, and profile routes onto the shared client.
- Why it changed: P2-11 calls for centralized backend origin handling, consistent credentials, and consistent backend error messages without forcing every route to hand-roll `fetch` response parsing.
- Ticket(s): `ticket/P2-11-normalize-api-client-usage.md`

## Files Touched

- `frontend/src/lib/api/client.ts`
- `frontend/src/routes/admin/+page.svelte`
- `frontend/src/routes/forum/+page.svelte`
- `frontend/src/routes/forum/new/+page.svelte`
- `frontend/src/routes/forum/post/+page.svelte`
- `frontend/src/routes/profile/create/+page.svelte`
- `frontend/src/routes/profile/edit/+page.svelte`
- `frontend/src/routes/validation/+page.svelte`

## Implementation Notes

- `apiFetch` now throws `ApiError` with `detail`, `message`, text response bodies, or a fallback in that order.
- Forum list/detail/create, admin reports/deletes, validation actions, and profile create/edit school/profile mutations now use `apiFetch`, so credentials and origin handling are shared.
- Direct `fetch` calls remain where route-specific behavior is clearer, including auth form pages with progressive server fallbacks, public homepage/contact/register calls, and the teacher image/share page.

## Verification

Commands run:

```bash
npm --prefix frontend run check
npx playwright test src/routes/forum/page.svelte.e2e.ts src/routes/forum/new/page.svelte.e2e.ts src/routes/forum/post/page.svelte.e2e.ts src/routes/admin/page.svelte.e2e.ts src/routes/profile/create/page.svelte.e2e.ts src/routes/profile/edit/page.svelte.e2e.ts src/routes/validation/page.svelte.e2e.ts
npm --prefix frontend run test:e2e
INTEGRATION_WORKERS=1 npm --prefix frontend run test:integration
scripts/run-all-tests.sh --quick
```

Results:

- Passed: Svelte check found 0 errors and 0 warnings.
- Passed: focused Playwright route coverage passed 36 tests.
- Passed: full frontend Playwright E2E passed 96 tests.
- Passed: one-worker frontend integration passed 14 tests.
- Passed: quick gate passed Svelte check, frontend lint, and Python static tests.

## Known Issues

- The remaining direct `fetch` inventory is intentional for now; those calls are either public, route-specific, or tied to progressive form behavior that is easier to audit locally.

## Next Best Step

- Proceed to P2-12 Clean Test Warning Noise.
