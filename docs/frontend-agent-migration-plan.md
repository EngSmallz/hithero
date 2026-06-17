# Frontend Agent Migration Plan

This document is the operational plan for agents modernizing the Homeroom Heroes frontend. It assumes the target frontend is SvelteKit with TypeScript and the existing FastAPI app remains the backend API during migration.

Use this file when implementing frontend migration work. The higher-level context lives in:

- `docs/modernization-plan.md`
- `docs/frontend-modernization-plan.md`

## Mission

Move Homeroom Heroes from repeated static HTML pages served by FastAPI into a modern SvelteKit frontend while preserving current behavior, clean URLs, SEO value, and test coverage.

The priority order is:

1. Preserve production behavior.
2. Improve crawlable public pages with server-rendered HTML.
3. Reduce repeated HTML, JavaScript, and CSS through components.
4. Keep migration batches small enough to review.
5. Defer backend restructuring until the frontend route ownership is clear.

## Hard Rules

- Do not turn the public site into a client-only SPA.
- Do not remove existing FastAPI page routes until replacement routes and redirects are tested.
- Do not rewrite backend business logic as part of frontend migration tasks.
- Do not introduce a second frontend framework without explicit approval.
- Do not copy repeated page header, footer, form, or auth logic into new Svelte pages.
- Do not rely on JavaScript-only rendering for indexable page body content.
- Do not add secrets, API keys, or environment-specific URLs to committed frontend files.
- Do not delete existing tests to make migration easier.

## Definition Of Done For Any Migrated Page

A migrated page is done only when all of these are true:

- It exists as a SvelteKit route.
- It preserves the intended clean URL.
- It renders meaningful HTML on the first server response when public/indexable.
- It has a unique title and meta description.
- It has a canonical URL.
- It has accessible landmarks, headings, labels, and focus states.
- It works at mobile and desktop widths.
- It uses shared components for repeated layout and controls.
- It does not include copied inline auth/navigation JavaScript.
- Playwright coverage exists for the primary user path.
- Legacy links in migrated source are removed or intentionally documented.
- Existing FastAPI/API behavior remains compatible.

## Recommended Work Sequence

### Step 1: Confirm Baseline

Before frontend work:

```bash
make test-static
make test-e2e
```

If a test fails before your changes, document it and avoid mixing that failure into migration work.

### Step 2: Create Frontend App

Create `frontend/` as a SvelteKit app with TypeScript.

Recommended setup choices:

- SvelteKit.
- TypeScript.
- ESLint.
- Prettier.
- Playwright or integration with the existing Playwright setup.
- No demo app content.

Expected initial files:

```text
frontend/
  src/
    lib/
    routes/
      +layout.svelte
      +error.svelte
      +page.svelte
    app.html
  static/
  package.json
  svelte.config.js
  vite.config.ts
```

Do not move existing backend files during this step.

### Step 3: Add Shared Frontend Foundation

Add these before migrating many pages:

```text
frontend/src/lib/components/Header.svelte
frontend/src/lib/components/Footer.svelte
frontend/src/lib/components/PageShell.svelte
frontend/src/lib/components/Seo.svelte
frontend/src/lib/components/Button.svelte
frontend/src/lib/components/FormField.svelte
frontend/src/lib/components/Alert.svelte
frontend/src/lib/api/client.ts
frontend/src/lib/api/types.ts
frontend/src/lib/routes.ts
frontend/src/lib/styles/app.css
```

Minimum component responsibilities:

- `Header`: public navigation, mobile navigation, auth-aware button slots or state.
- `Footer`: repeated footer links and copyright.
- `PageShell`: consistent max width, spacing, and page structure.
- `Seo`: page title, description, canonical, Open Graph tags.
- `Button`: consistent button and link-button styling.
- `FormField`: label, help text, error text, and input slot.
- `Alert`: success, warning, error, and info messages.

Keep components boring. A future backend-heavy contributor should be able to read them without knowing advanced frontend patterns.

### Step 4: Configure Backend Access

The frontend needs one clear way to call FastAPI.

Use an environment variable for the backend origin:

```text
PUBLIC_BACKEND_ORIGIN=http://localhost:8000
```

For server-side SvelteKit loads, use a server-only backend origin when needed. Do not expose secrets to the browser.

Create a tiny API client wrapper that:

- Builds URLs consistently.
- Sends credentials when cookies are required.
- Converts non-2xx responses into typed errors.
- Avoids each page hand-writing fetch boilerplate.

### Step 5: Migrate The First Vertical Slice

The first slice should prove routing, layout, metadata, assets, API integration, and tests.

Recommended first slice:

1. `/`
2. `/about`
3. Shared layout/header/footer.
4. SEO metadata.
5. One browser test for desktop.
6. One browser test for mobile navigation.

Do not start with the forum, auth, profile edit, validation, or admin pages.

### Step 6: Migrate Public Static Pages

Migrate in this order:

1. `/`
2. `/about`
3. `/contact`
4. `/partners`
5. `/terms`
6. `/login`
7. `/forgot`
8. `/register`

For each page:

- Copy the visible content intentionally, not mechanically.
- Replace repeated header/footer with shared components.
- Replace repeated form styling with shared form components.
- Add metadata.
- Add a Playwright smoke test.
- Confirm old static page still works until final redirect cleanup.

### Step 7: Migrate SEO-Critical Dynamic Pages

Migrate:

- `/teachers`
- `/teacher/[urlId]`

These pages matter most for indexing. They should be SSR, not client-only.

Teacher profile requirements:

- Server-render teacher name, school, story, and wishlist link if public.
- Return real 404 when the teacher does not exist.
- Use canonical URL for the final profile route.
- Include Open Graph data suitable for sharing.
- Avoid exposing private profile edit fields on public pages.

Teacher directory requirements:

- Server-render useful initial content.
- Keep filters crawlable where practical.
- Use clean URLs for filter states only if those pages have lasting SEO value.

### Step 8: Migrate Authenticated App Pages

Migrate only after public pages and shared auth handling are stable.

Routes:

- `/profile/create`
- `/profile/edit`
- `/update-password`
- `/validation`
- `/admin`
- `/forum`
- `/forum/new`
- `/forum/post/[id]`

Private page rules:

- Keep out of sitemap.
- Use noindex when a page can render HTML but should not be indexed.
- Redirect unauthenticated users consistently.
- Keep role behavior covered by tests.

### Step 9: Legacy Route Cleanup

After a route is migrated and verified:

1. Keep the clean URL as canonical.
2. Redirect safe legacy `/pages/*.html` paths.
3. Keep direct serving only for query-sensitive or intentionally deferred legacy pages.
4. Update sitemap.
5. Add or update redirect tests.
6. Remove stale static HTML only after a complete replacement is proven.

## Page Migration Checklist

Use this checklist for every page migration PR or commit.

```text
[ ] Route exists in SvelteKit.
[ ] Page content matches or intentionally improves current behavior.
[ ] Shared Header/Footer/PageShell are used.
[ ] No copied inline auth/nav JavaScript.
[ ] Public page has title, description, canonical, and Open Graph tags.
[ ] Public page renders useful body content server-side.
[ ] Forms have labels, validation messages, and stable submit behavior.
[ ] Mobile layout checked at 390px width.
[ ] Desktop layout checked around 1280px width.
[ ] Playwright test added or updated.
[ ] Legacy links removed from migrated page source.
[ ] Sitemap decision made.
[ ] FastAPI compatibility preserved.
```

## Frontend Coding Standards

### Svelte Components

- Use component props for real variation.
- Do not create abstractions for one-off markup.
- Prefer readable markup over clever logic.
- Keep page components focused on page composition.
- Put reusable logic under `src/lib`.

### TypeScript

- Define API response types in `src/lib/api/types.ts`.
- Avoid `any` unless there is a short comment explaining why.
- Parse and validate unknown API data at boundaries where practical.

### CSS And Styling

- Prefer shared classes/components for repeated controls.
- Keep layout responsive by default.
- Use stable image dimensions or aspect ratios.
- Keep focus states visible.
- Do not ship accidental Markdown tokens in class strings.
- Do not create a new color palette per page.

### Forms

- Use real `<form>` elements.
- Use real `<button type="submit">`.
- Every input needs a label.
- Preserve user-entered values after validation failures when practical.
- Show success and failure states clearly.

### Accessibility

- Use semantic HTML before ARIA.
- Keep heading order logical.
- Links navigate. Buttons perform actions.
- Modals must manage focus before they are considered done.
- Interactive controls must be keyboard usable.

## SEO Requirements For Public Pages

Every public page should define:

```text
title
description
canonical URL
Open Graph title
Open Graph description
Open Graph image where useful
```

Public pages should also:

- Use normal anchor tags for internal links.
- Return correct HTTP status codes.
- Avoid duplicate canonical content.
- Avoid hiding core content behind click-only interactions.
- Keep sitemap entries limited to canonical public URLs.

## Testing Plan

Keep tests close to user behavior.

Minimum Playwright coverage:

- Public page loads.
- Header navigation works.
- Mobile menu opens and navigates.
- Legacy redirects land on clean URLs.
- Auth button visibility changes by role.
- Private pages reject unauthenticated users.
- Important forms show success and error states.
- Dynamic profile 404 behavior works.

Add metadata tests for:

- Title.
- Meta description.
- Canonical link.
- No `/pages/*.html` links in rendered public pages.

## Suggested Commit Order

Use small commits.

1. Scaffold frontend.
2. Add shared layout/components.
3. Add frontend test harness.
4. Port homepage.
5. Port about/partners/terms.
6. Port contact.
7. Port login/forgot/register.
8. Port teacher directory.
9. Port teacher profile SSR.
10. Port authenticated pages.
11. Clean legacy route serving.

Each commit should leave the app runnable.

## Agent Handoff Notes

When stopping work, leave a short note in the final response with:

- Routes migrated.
- Tests run.
- Known issues.
- Next recommended route or component.
- Any intentional legacy behavior left in place.

Do not leave a half-migrated route as the canonical URL unless it is clearly marked and tested.

## First Agent Task Recommendation

The next implementation task should be:

1. Scaffold `frontend/` with SvelteKit and TypeScript.
2. Add shared layout/header/footer/SEO components.
3. Port `/about` first as the smallest public page proof.
4. Add one Playwright test that verifies server-rendered title, visible content, and mobile navigation.

This keeps the blast radius low while proving the framework, routing, layout, metadata, and test pattern.
