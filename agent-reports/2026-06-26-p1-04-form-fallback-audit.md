# P1-04 Form Fallback Audit Report

## Summary

Implemented `ticket/P1-04-svelte-form-fallback-audit.md`: migrated unsafe native Svelte form submissions away from direct FastAPI JSON endpoints and onto SvelteKit-owned actions. The goal was not to make every interaction fully no-JS, but to ensure every form has an intentional fallback and no native submit strands a user on raw API JSON.

## What Changed

- Added shared action helpers in `frontend/src/lib/server/form-actions.ts` for cookie forwarding, API error messages, and response message extraction.
- Added SvelteKit actions for `/contact`, `/forgot`, `/login`, and `/reset-password`.
- Extended existing server files with actions for `/register`, `/update-password`, `/profile/create`, and `/profile/edit`.
- Repointed native `action` attributes in the affected Svelte pages from FastAPI endpoints to Svelte routes or named Svelte actions.
- Added `frontend/src/routes/form-fallbacks.e2e.ts` to cover no-JS fallback behavior for the highest-risk public/account flows.
- Updated `docs/form-fallback-matrix.md` so every audited form is classified as native-safe, SvelteKit-action safe, or intentionally JS-required.

## Why

Several migrated pages had semantic HTML forms with hydrated `onsubmit` handlers, but their native `action` still pointed at FastAPI JSON endpoints. If hydration was slow or JavaScript was disabled, the browser could submit directly to API routes such as `/profile/forgot_password/` and display JSON instead of a Svelte page. `P0-01` fixed this for `/forum/new`; `P1-04` applies the same modernization integrity rule across the remaining form surface.

## Important Decisions

- reCAPTCHA forms (`/contact`, `/register`) cannot truly complete without JavaScript because no token is available. Their fallback is a Svelte-owned error explaining that JavaScript/reCAPTCHA is required, rather than a fake successful no-JS flow.
- Login fallback proxies FastAPI directly, copies the backend `session` cookie into the SvelteKit response, and redirects to `/profile/create`, the safe `redirect` target, or `/`.
- Authenticated profile/password actions forward the browser cookie to FastAPI so backend auth and mutation logic remain canonical.
- `/forum/post` inline edits/comments and `/admin` tools remain intentionally JS-required app interactions. They have no backend `action`, so native submit does not expose raw JSON.

## Verification

Passed:

```bash
npm --prefix frontend run check
npm --prefix frontend run lint
npx playwright test src/routes/form-fallbacks.e2e.ts
scripts/run-all-tests.sh --quick
```

Focused affected-route batch:

```bash
npx playwright test src/routes/login/page.svelte.e2e.ts src/routes/forgot/page.svelte.e2e.ts src/routes/reset-password/page.svelte.e2e.ts src/routes/register/page.svelte.e2e.ts src/routes/update-password/page.svelte.e2e.ts src/routes/profile/create/page.svelte.e2e.ts src/routes/profile/edit/page.svelte.e2e.ts
```

Result: 34/35 passed. The only failure was `/forgot` mobile navigation visibility; it passed immediately on direct rerun with:

```bash
npx playwright test src/routes/forgot/page.svelte.e2e.ts -g "opens mobile navigation"
```

Not run: full `scripts/run-all-tests.sh` after this P1 slice.

## Known Caveats

- The worktree already contained many unrelated dirty/untracked files from earlier modernization work. This report only covers the P1-04 additions and edits.
- Registration no-JS coverage asserts the native action stays on `/register`; a full no-JS submit can be blocked by native required selects if the test DB has no school options, which is still safe because no FastAPI JSON endpoint is exposed.

## Next Best Step

Move to `P1-05: Close Forum DB Sessions On All Error Paths`, then run focused backend/forum tests before the full modernization gate.
