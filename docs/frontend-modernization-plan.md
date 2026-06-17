# Frontend Modernization Plan

This plan covers the frontend framework decision, migration strategy, conventions, and first implementation milestones.

## Framework Decision

Use SvelteKit with TypeScript.

SvelteKit is the best fit for this team because it gives modern frontend structure without requiring the full React ecosystem. It provides file-based routing, server-side rendering by default, per-page rendering controls, form actions, layouts, and a small component model that stays close to normal HTML, CSS, and JavaScript.

## Why SvelteKit

- Server-rendered pages by default for SEO and fast first load.
- Routes are easy to reason about: `src/routes/about/+page.svelte` becomes `/about`.
- Components are straightforward for backend-heavy contributors to read.
- TypeScript catches data and prop mistakes early.
- Public pages, dynamic SSR pages, and authenticated app pages can live in one project.
- Forms can start as normal HTML forms and later get enhanced JavaScript behavior.
- Less framework ceremony than modern Next.js for a small team.

## Why Not Next.js First

Next.js is a strong framework and the safer hiring-market default, but it carries more React-specific complexity:

- React hooks.
- Server Components versus Client Components.
- App Router conventions.
- Caching and invalidation rules.
- More ecosystem choices around state, forms, and styling.

Those are fine tradeoffs for an experienced frontend team. They are less helpful for a backend developer and a firmware test engineer trying to make steady progress.

## Why Not Astro First

Astro is excellent for content-heavy sites and very fast static pages. It is less direct for an app with auth, forms, forum flows, admin pages, and many interactive states.

Astro may be useful later if the marketing/public site is split from the authenticated app. For now, SvelteKit is a better single frontend framework.

## Frontend Principles

1. Public pages must render meaningful HTML on the server.
2. Normal links and forms should work before adding client-side enhancement.
3. Components should remove repetition, not hide simple markup behind clever abstractions.
4. Styling should be consistent through shared components and tokens.
5. JavaScript should be loaded only where interaction requires it.
6. Accessibility is part of the definition of done.
7. Tests should describe user behavior, not implementation trivia.

## Initial Frontend Structure

Recommended starting structure:

```text
frontend/
  src/
    lib/
      api/
        client.ts
        types.ts
      components/
        Button.svelte
        Card.svelte
        FormField.svelte
        Header.svelte
        Footer.svelte
        Seo.svelte
      styles/
        app.css
      routes.ts
    routes/
      +layout.svelte
      +layout.ts
      +error.svelte
      +page.svelte
      about/
        +page.svelte
      contact/
        +page.svelte
      login/
        +page.svelte
      teacher/
        [urlId]/
          +page.server.ts
          +page.svelte
  static/
  tests/
  package.json
  svelte.config.js
  vite.config.ts
```

## Backend Integration

Keep FastAPI as the backend API during the frontend migration.

Short-term:

- SvelteKit calls FastAPI endpoints.
- Auth remains cookie/session based.
- Existing FastAPI routes remain available.
- Legacy page routes stay until each replacement is proven.

Medium-term:

- Add API routes that return clean JSON for frontend needs.
- Avoid frontend pages scraping or depending on legacy HTML.
- Add typed frontend API wrappers in `src/lib/api`.

Long-term:

- FastAPI stops owning browser page rendering.
- FastAPI owns API, auth, database, jobs, email, and integrations.

## Page Migration Map

| Current file | New route | Rendering |
| --- | --- | --- |
| `homepage.html` | `/` | prerender or SSR |
| `about.html` | `/about` | prerender |
| `contact.html` | `/contact` | SSR or prerender plus form action |
| `partners.html` | `/partners` | prerender |
| `terms_conditions.html` | `/terms` | prerender |
| `index.html` | `/teachers` | SSR |
| `teacher.html` | `/teacher/[urlId]` | SSR |
| `login.html` | `/login` | SSR |
| `register.html` | `/register` | SSR |
| `forgot.html` | `/forgot` | SSR |
| `reset_password.html` | `/reset-password` | SSR, query/token aware |
| `forum.html` | `/forum` | SSR or authenticated app route |
| `post.html` | `/forum/post/[id]` | SSR if public, noindex if private |
| `create_post.html` | `/forum/new` | authenticated app route |
| `create.html` | `/profile/create` | authenticated app route |
| `edit_teacher.html` | `/profile/edit` | authenticated app route |
| `update_password.html` | `/update-password` | authenticated app route |
| `validation.html` | `/validation` | authenticated app route, noindex |
| `admin.html` | `/admin` | authenticated app route, noindex |
| `403.html` | `/403` | real 403 page |
| `404.html` | `/404` | real 404 page |

## Design System Starter

Start small. Do not create a giant design system.

Create these first:

- `Header`
- `Footer`
- `PageShell`
- `Seo`
- `Button`
- `IconButton`
- `Card`
- `FormField`
- `TextInput`
- `Select`
- `Textarea`
- `Alert`
- `LoadingState`
- `EmptyState`

Use shared CSS variables or Tailwind theme values for:

- Brand colors.
- Text colors.
- Border colors.
- Focus ring.
- Spacing scale.
- Border radius.
- Shadow levels.
- Page max widths.

## Styling Rules

- Mobile layout comes first.
- Avoid copied Tailwind strings across many pages.
- Use components for repeated controls and surfaces.
- Every interactive control needs a visible focus state.
- Buttons perform actions. Links navigate.
- Form fields need labels, error text, and help text where useful.
- Avoid layout shifts by giving images and cards stable dimensions.
- Do not hide core content behind JavaScript-only rendering on public pages.

## SEO Rules

Every indexable page needs:

- Server-rendered body content.
- Unique `<title>`.
- Unique meta description.
- Canonical URL.
- Open Graph metadata.
- Correct HTTP status.
- Inclusion in sitemap only when public and useful.

Private pages need:

- No sitemap entry.
- `noindex` where appropriate.
- Correct auth handling.

## Testing Strategy

Use Playwright as the main frontend safety net.

Test categories:

- Public page loads.
- Mobile navigation.
- Form validation and submission behavior.
- Auth button visibility by role.
- Redirects from legacy URLs.
- Metadata for indexable pages.
- 404 and 403 behavior.

Keep tests readable enough that the test engineer can own them. Prefer user-facing locators and visible text over brittle CSS selectors.

## First Vertical Slice

The first implementation slice should prove the full pattern without migrating the whole site.

Recommended slice:

1. Create SvelteKit app in `frontend/`.
2. Add shared layout, header, footer, and SEO component.
3. Port homepage to `/`.
4. Port `/about`.
5. Proxy or call FastAPI for any required homepage data.
6. Add Playwright tests for desktop and mobile.
7. Verify rendered HTML contains title, meta description, canonical URL, and visible page content without client JavaScript.

After that slice is stable, port page groups in small batches.

## Contributor Workflow

For contributors new to frontend:

1. Edit one route or component at a time.
2. Run the frontend dev server.
3. Check mobile width and desktop width.
4. Run the focused Playwright test.
5. Avoid adding new global JavaScript.
6. Ask whether a repeated pattern should become a component before copying it a third time.

## Open Decisions

- Final deployment topology: one host with reverse proxy, or separate frontend/backend deployments.
- Final teacher profile URL shape.
- Whether forum posts should be public/indexable or private/noindex.
- Whether contact/register/login forms should post to SvelteKit actions that call FastAPI, or directly to FastAPI.
- Whether Tailwind remains the styling base or is wrapped behind mostly custom CSS classes.
