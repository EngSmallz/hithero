# P0-01: Make `/forum/new` Create-Post Flow Progressively Safe

## Problem

The `/forum/new` Svelte route has a client-side `onsubmit` handler that posts to FastAPI and redirects to `/forum/post?id=...`. The native form `action` points directly to `/forum/create_post`, so if the form is submitted before hydration attaches, or if JavaScript fails, the user can land on raw backend JSON.

This is a modernization blocker because clean Svelte routes should remain the browser-facing experience.

## Scope

- Update the create-post flow so the success path lands on the clean Svelte forum detail route.
- Preserve the existing hydrated experience.
- Ensure slow-hydration and no-JS behavior do not strand users on backend JSON.
- Keep auth behavior consistent with the rest of migrated authenticated routes.

## Acceptance Criteria

- Submitting `/forum/new` with normal JavaScript creates the post and navigates to `/forum/post?id=<id>`.
- Submitting before hydration completes does not leave the user on `/forum/create_post` JSON.
- A no-JS submit either redirects to the clean post detail route or shows a useful Svelte-owned fallback page.
- Existing `/forum/new` tests pass.
- Add or update coverage that proves the fallback behavior, not only the hydrated path.

## Verification

- `npm --prefix frontend run test:e2e`
- A focused Playwright test for slow-hydration or JavaScript-disabled form submission.
- Manual check: submit `/forum/new` with JavaScript disabled or artificially delayed.
