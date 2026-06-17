# Homeroom Heroes Modernization Plan

This plan defines the direction for modernizing Homeroom Heroes from a single-file FastAPI app with repeated static HTML into a maintainable, testable web product.

## Current State

- `app.py` contains routing, models, business logic, scheduled jobs, auth, page serving, and forum APIs in one file.
- `pages/*.html` contains repeated markup, repeated navigation, repeated scripts, and inline JavaScript.
- Some shared CSS and JavaScript extraction has started.
- Clean URLs and legacy redirects are partially in place.
- Regression coverage now exists for static HTML contracts, clean routes, and browser smoke tests.

## Goals

1. Make the public site feel modern, trustworthy, fast, and mobile-first.
2. Serve indexable public pages with meaningful server-rendered HTML for Google and other crawlers.
3. Replace repeated static HTML with reusable frontend components.
4. Keep FastAPI as the backend API while the frontend is migrated.
5. Give backend-heavy contributors clear conventions that reduce frontend guesswork.
6. Preserve current behavior during migration with tests and redirects.

## Non-Goals

- Do not rewrite the backend first.
- Do not create a client-only single-page app for public/indexable pages.
- Do not change database schema or auth behavior as part of the first frontend migration unless required.
- Do not remove legacy `/pages/*.html` routes until replacement routes and redirects are verified.

## Target Architecture

The recommended target is:

- `frontend/`: SvelteKit + TypeScript for pages, layouts, components, forms, metadata, and SSR.
- `backend/`: FastAPI API, eventually split into routers, services, models, schemas, and jobs.
- `tests/`: Playwright browser tests plus focused backend/API tests.

FastAPI should gradually stop serving static page HTML. It should expose data and actions through explicit API routes. SvelteKit should own browser-facing pages and render public pages on the server.

## Rendering Policy

Use the simplest rendering mode that matches the page.

- Static or mostly static public pages: prerender or SSR.
- Dynamic public pages, such as teacher profiles: SSR.
- Authenticated app pages: SSR where useful, client interactivity as needed.
- Private/admin pages: noindex, not included in sitemap.
- Error pages: real HTTP statuses, especially `404`, `403`, and `401`.

Public pages must include:

- Unique title.
- Meta description.
- Canonical URL.
- Open Graph title, description, and image when appropriate.
- Crawlable links using normal `<a href="...">` elements.
- Meaningful initial HTML without requiring client JavaScript for core content.

## Route Policy

Clean URLs are canonical.

- Good: `/`, `/teachers`, `/teacher/some-url-id`, `/forum/post/some-id`, `/login`.
- Legacy: `/pages/index.html`, `/pages/teacher.html`, `/pages/login.html`.

Legacy URLs should redirect when safe. Query-sensitive URLs need individual review before redirecting.

Sitemaps should include only canonical public URLs that should be indexed.

## Migration Phases

### Phase 0: Stabilize Current Site

- Finish clean URL redirects for HEAD and GET.
- Document modernization direction.
- Fix obvious HTML defects, including literal `**md:hidden**` class strings.
- Keep current tests passing.

### Phase 1: Frontend Foundation

- Create `frontend/` SvelteKit project with TypeScript.
- Add shared layout, header, footer, navigation, and SEO metadata helpers.
- Add design tokens for color, spacing, typography, focus states, and form states.
- Configure Playwright against the frontend.
- Add local development commands that start frontend and backend together.

### Phase 2: Public Page Migration

Migrate low-risk public pages first:

1. `/`
2. `/about`
3. `/contact`
4. `/partners`
5. `/terms`
6. `/login`
7. `/register`
8. `/forgot`

Each migrated page should preserve the canonical URL, pass browser tests, and remove duplicated markup.

### Phase 3: SEO-Critical Dynamic Pages

- Migrate teacher profile pages to SSR.
- Decide final public URL shape for teacher profiles.
- Add structured metadata where useful.
- Ensure not-found teacher profiles return real 404s.
- Generate a sitemap from canonical routes and public data.

### Phase 4: Authenticated App Pages

- Migrate profile create/edit, update password, validation, admin, and forum flows.
- Use progressive enhancement for forms where practical.
- Keep private pages out of sitemap.
- Ensure unauthenticated access returns or redirects to the correct status/page.

### Phase 5: Backend Cleanup

After frontend route ownership is clear:

- Split `app.py` into FastAPI routers.
- Move database models and schemas into dedicated modules.
- Move business logic into services.
- Move scheduled jobs into jobs/tasks modules.
- Add API response models and tighter validation.
- Address SQLAlchemy and Pydantic deprecation warnings.

## Quality Gates

Every migrated route should have:

- Browser test for load/navigation.
- Mobile viewport coverage for layout basics.
- Test for expected title and canonical metadata.
- Test for correct auth behavior where relevant.
- No legacy `/pages/*.html` links in migrated source.
- No inline copy-pasted auth/nav JavaScript.

Before removing a legacy page:

- Clean route exists.
- Redirect exists for safe legacy URL.
- Sitemap uses clean URL.
- Tests prove old and new behavior.

## References

- Google JavaScript SEO basics: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- Google dynamic rendering guidance: https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering
- SvelteKit routing: https://svelte.dev/docs/kit/routing
- SvelteKit page options: https://svelte.dev/docs/kit/page-options
- SvelteKit SEO: https://svelte.dev/docs/kit/seo
- Playwright: https://playwright.dev/docs/intro
