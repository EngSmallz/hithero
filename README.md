# Homeroom Heroes

Homeroom Heroes is moving from a single FastAPI app that served HTML pages and
browser JavaScript to a SvelteKit UI backed by a FastAPI API. The move keeps
the existing data, URLs, session shape, API contracts, and integrations; it
changes where that behavior is implemented.

## Current state

Two applications run during the transition:

```text
http://127.0.0.1:5173  SvelteKit: the new UI in frontend/
        │
        │ JSON requests with the session cookie
        ▼
http://127.0.0.1:8000  FastAPI: API, site endpoints, and old-URL redirects
        ▼
SQLite locally; configured production database when deployed
```

Use `make local`, then browse the Vite address (normally port 5173). FastAPI
does not serve application pages; deployment routing must send page requests
to SvelteKit and API requests to FastAPI. Old `/pages/*.html` links retain a
small redirect map while external traffic is migrated.

## Old site → current code

| Original location | Current location | Reason for the move |
| --- | --- | --- |
| `app.py` | `backend/main.py` creates FastAPI; `backend/api/composition.py` wires dependencies and routers; `app.py` remains a compatibility import. | Startup is explicit and testable; new code has a clear home. |
| `pages/*.html` | `frontend/src/routes/**/+page.svelte` | Filesystem routes keep a page's UI, data loading, form handling, and E2E tests together. |
| Repeated HTML header/footer | `frontend/src/routes/+layout.svelte`, `frontend/src/lib/components/Header.svelte`, `Footer.svelte` | One shared accessible shell rather than duplicated markup. |
| `static/js/auth.js` | `frontend/src/routes/+layout.server.ts`, `frontend/src/lib/server/auth.ts`, backend auth/policies | The UI knows who is signed in, but FastAPI remains the real authorization boundary. |
| `static/js/forms.js` and inline `fetch` | Route `+page.server.ts` actions, `frontend/src/lib/api/client.ts`, and `frontend/src/lib/server/api.ts` | Cookie forwarding, JSON errors, redirects, and form failures follow one tested pattern. |
| `static/js/school-dropdowns.js` | Register/profile/admin Svelte routes plus `frontend/src/lib/api/options.ts` | Dependent fields are typed and live next to the forms that use them. |
| Inline CSS/Tailwind CDN | Local Tailwind/Vite setup, `frontend/src/lib/styles/app.css`, shared Svelte components | Styles are built with the app and reusable. Legacy CSS remains only while legacy pages remain. |
| SQL and business rules mixed with endpoints | `backend/routers/`, `services/`, and `repositories/` | HTTP, business rules, and SQL can be changed/tested independently. |
| Email/reCAPTCHA/X calls in web code | `backend/integrations/` and `backend/jobs/` | External effects are isolated and deterministic in test mode. |

### Detailed page migration map

All Svelte routes also run through the shared layout and its current-profile
load. `+page.server.ts` means the route has server-side data loading and/or
form actions; plain `+page.svelte` means a static or browser-driven page. The
legacy source files listed below have been retired; this is a historical map.

| Legacy page | Legacy browser code | SvelteKit replacement | Backend contract used by the replacement |
| --- | --- | --- | --- |
| `homepage.html` → `/` | Inline homepage fetches; `auth.js` | `routes/+page.svelte`, `routes/+page.server.ts` | `/spotlight/teacher`, `/promo/get_promo_info/`, `/api/random_teacher/` |
| `index.html` → `/teachers` | `school-dropdowns.js`; inline search | `routes/teachers/+page.svelte`, `+page.server.ts` | `/api/teachers/` with filter/page query; directory option endpoints |
| `teacher.html` → `/teacher`, `/teacher/<urlId>` | Inline profile/image code; `auth.js` | `routes/teacher/+page.svelte`, `+page.server.ts`; `routes/teacher/[urlId]/+page.svelte`, `+page.server.ts` | `/api/current_teacher/`, `/api/teacher/<urlId>/`, `/api/get_teacher_info/`, image and URL update endpoints |
| `about.html` → `/about` | `auth.js` | `routes/about/+page.svelte` | Shared layout profile load only |
| `partners.html` → `/partners` | `auth.js` | `routes/partners/+page.svelte` | Shared layout profile load only |
| `terms_conditions.html` → `/terms` | None | `routes/terms/+page.svelte` | None beyond shared layout |
| `wishlist_setup.html` → `/wishlist-setup` | None | `routes/wishlist-setup/+page.svelte` | None beyond shared layout |
| `contact.html` → `/contact` | `contact-form.js`; reCAPTCHA | `routes/contact/+page.svelte`, `+page.server.ts` | `/api/contact_us/` |
| `register.html` → `/register` | `forms.js`, `school-dropdowns.js`; reCAPTCHA | `routes/register/+page.svelte`, `+page.server.ts` | `/profile/register/`, `/api/get_states/`, counties/districts/schools options |
| `login.html` → `/login` | `forms.js` | `routes/login/+page.svelte`, `+page.server.ts` | `/profile/login/`; return URL is preserved |
| `forgot.html` → `/forgot` | `forms.js` | `routes/forgot/+page.svelte`, `+page.server.ts` | `/profile/forgot_password/` |
| `reset_password.html` → `/reset-password` | `forms.js` | `routes/reset-password/+page.svelte`, `+page.server.ts` | `/profile/reset_password/`; token stays in the query string |
| `update_password.html` → `/update-password` | `forms.js` | `routes/update-password/+page.svelte`, `+page.server.ts` | `/profile/update_password/`; requires a signed-in user |
| `create.html` → `/profile/create` | Inline profile form; `school-dropdowns.js` | `routes/profile/create/+page.svelte`, `+page.server.ts` | `/profile/create_teacher_profile/`, `/api/profile/`, school options |
| `edit_teacher.html` → `/profile/edit` | Inline mutation calls; `school-dropdowns.js` | `routes/profile/edit/+page.svelte`, `+page.server.ts` | `/profile/myinfo/`, `/api/current_teacher/`, profile mutation and school-change endpoints |
| `forum.html` → `/forum` | Inline list/auth code | `routes/forum/+page.svelte`, `+page.server.ts` | `/forum/get_posts`; requires a signed-in forum role |
| `create_post.html` → `/forum/new` | Inline post creation | `routes/forum/new/+page.svelte`, `+page.server.ts` | `/forum/create_post`; requires a signed-in forum role |
| `post.html` → `/forum/post?id=…` | Inline comments, votes, edits, deletion | `routes/forum/post/+page.svelte`, `+page.server.ts` | Forum get/comment/vote/edit/delete endpoints; query `id` is preserved |
| `validation.html` → `/validation` | Inline validation actions | `routes/validation/+page.svelte`, `+page.server.ts` | Validation list, approve/delete/report/email, school-change review endpoints |
| `admin.html` → `/admin` | Inline report/delete/options calls | `routes/admin/+page.svelte`, `+page.server.ts` | Admin report, profile deletion, indexed school option endpoints |
| `403.html`, `404.html` → `/403`, `/404` | None | `routes/403/+page.server.ts`, `routes/404/+page.server.ts`, shared `routes/+error.svelte` | No business API call |

Every `/pages/*.html` URL redirects to its clean equivalent through
`backend/routers/redirects.py`. Public assets, homepage promotion/spotlight
APIs, and externally shared teacher links live in `backend/routers/site.py`.
The public `/sitemap.xml` is generated per request from the canonical static
URL set plus currently eligible teacher profiles; it uses short HTTP caching
and does not publish unverifiable `lastmod` values. The static robots files
continue to point crawlers at that canonical sitemap URL.

## Backend: where behavior belongs

| Layer | Files | Responsibility |
| --- | --- | --- |
| Application | `backend/main.py`, `backend/core/settings.py` | Create FastAPI, database resources, provider adapters, middleware, `/healthz`, and `/readyz`. |
| Composition | `backend/api/composition.py`, `backend/api/register.py` | Construct dependencies and register grouped routes. This is the wiring diagram. |
| Router (controller) | `backend/routers/*.py` | Parse HTTP input, require roles/ownership, call a use case, return the established HTTP contract. |
| Service | `backend/services/*.py` | Apply domain rules and coordinate multi-step work. Example: school-change rules and transactional profile changes. |
| Repository | `backend/repositories/*.py` | SQLAlchemy queries and session/transaction lifecycle. No HTTP decisions. |
| Database | `backend/db/models.py`, `backend/db/session.py` | SQLAlchemy models; choose and construct database engine/session factory. |
| Core | `backend/core/*.py` | Session auth, CSRF, policies, errors, observability, serialization. |
| Integration | `backend/integrations/*.py` | Email, reCAPTCHA, X, and file inspection adapters. |
| Jobs | `backend/jobs/*.py` | Existing scheduled notification behavior and its command runner. |
| Schemas | `backend/schemas/*.py` | Pydantic input/output contracts where a typed API shape is useful. |

The important rule is: **SvelteKit improves navigation and form UX; FastAPI
authorizes the action.** A browser can call an API without using the UI, so
the backend must enforce every role and ownership rule.

### A concrete request

For an edit to a teacher profile:

```text
profile/edit/+page.svelte        renders the form
profile/edit/+page.server.ts     loads data / forwards a form with the cookie
lib/server/api.ts + api/client.ts forwards request and normalizes JSON errors
routers/profile.py               selects the HTTP action and access check
services/profile_mutations.py    enforces rules and coordinates the use case
repositories/profile.py          performs SQLAlchemy work, one transaction when needed
db/models.py                     maps the stored data
```

This is the practical gain over a single file: a route does not need SQL
knowledge, a repository does not decide user-facing policy, and a UI component
does not become the only security check.

## Frontend: how SvelteKit is organized

| Pattern | Meaning |
| --- | --- |
| `src/routes/x/+page.svelte` | Rendered page for `/x`. |
| `src/routes/x/+page.server.ts` | Server-only load/action code for `/x`; can safely forward the incoming cookie. |
| `src/routes/teacher/[urlId]/` | Dynamic URL segment, e.g. `/teacher/alice-smith`. |
| `src/routes/+layout.svelte` | Shared page shell, skip link, header, footer, and global CSS. |
| `src/routes/+layout.server.ts` | Shared current-profile data for navigation. |
| `src/routes/+error.svelte` | Common failure UI. |
| `src/lib/components/` | Reusable UI: alerts, buttons, fields, shell, SEO, header/footer. |
| `src/lib/api/` | Typed API client, API types, and option parsing. |
| `src/lib/server/` | Cookie/header forwarding, server API helper, auth guards, form utilities. |

The route owns its visible state. Shared behavior is extracted only when more
than one route actually needs it.

## Data, security, and deployment

`backend/db/models.py` maps users, teachers, schools, forum content, votes,
reset tokens, spotlights, and school-change requests. `backend/db/session.py`
selects the database:

- `APP_ENV=test` → `TEST_DATABASE_URL` (SQLite by default).
- local development → `LOCAL_DATABASE_URL` (SQLite by default).
- deployment → `DATABASE_URL`, otherwise configured SQL Server variables.

`migrations/` holds Alembic history. Migrations are **not** applied at startup;
creating or applying production schema changes is a separate deployment
decision.

Sessions are HTTP-only, `SameSite=Lax`, secure outside local/test environments,
and normally last 14 days. CSRF middleware protects unsafe cookie-authenticated
requests. Test mode suppresses real email/X activity and accepts the configured
test reCAPTCHA token. Local frontend startup defaults to
`PUBLIC_RECAPTCHA_MODE=mock`, which renders the same local CAPTCHA control on
registration and contact forms instead of loading Google's domain-bound widget.
Deployment must configure `PUBLIC_BACKEND_ORIGIN`, HTTPS, and
`CORS_ALLOW_ORIGINS` consistently so browser cookies reach FastAPI.
See [AZURE_APP_SERVICE_PREP.md](AZURE_APP_SERVICE_PREP.md) for the deployment
preparation inventory and proof sequence.

## Run it

Install dependencies and the Playwright browser once:

```bash
make install-dev
```

Start the normal full stack:

```bash
make local
```

`make local` bootstraps the configured local SQLite database with its schema,
100 demo schools, and 50 public demo teacher profiles before delegating process
supervision to `scripts/start-local.sh`, which starts FastAPI and Vite and stops
both with `Ctrl-C`. The bootstrap is idempotent, SQLite-only, and does not run
Alembic migrations. `make dev-backend` and `make dev-frontend` remain available
for running one service at a time.

The local demo fixtures live in `scripts/fixtures/schools.csv` and
`scripts/fixtures/fake-public-teachers.csv`; they contain 100 schools and 50
obvious fake public teacher profiles.

For the disposable school-change manual flow, seed an alternate school into
the local SQLite database without applying migrations:

```bash
make seed-local-school
```

Start only a test-mode FastAPI backend:

```bash
make local-test
```

It uses `.tmp/local-test.sqlite`, clears inherited `DATABASE_URL`, and creates
and seeds the SQLite schema automatically. Initialize a disposable database
manually only when needed:

```bash
TEST_DATABASE_URL=sqlite:///./.tmp/local-test.sqlite make init-test-db
```

See [local-test-README.md](local-test-README.md) for test-stack details.

## Tests and retirement

| Command/location | Protects |
| --- | --- |
| `tests/test_*.py` | Backend contracts, services, repositories, security, provider adapters, and migration boundaries. |
| `tests/e2e/` | Browser checks for the FastAPI/legacy surface that still exists. |
| `frontend/src/routes/**/*.e2e.ts` | Svelte route and critical-form browser behavior. |
| `frontend/tests/integration/` | SvelteKit-to-FastAPI integration with isolated data. |
| `scripts/run-all-tests.sh` | Release-confidence gate; slow suites deliberately run in parallel. |

Useful focused commands:

```bash
make test-static
make test-e2e
make test-forum-api
make test-teachers-api
npm --prefix frontend run check
npm --prefix frontend run lint
npm --prefix frontend run test:e2e
npm --prefix frontend run test:integration
```

Do not delete old HTML, static JavaScript, legacy aliases, or their tests only
because a similar Svelte route exists. The manual acceptance gate and the
required final automated proof are in [GOLDEN_TARGET.md](GOLDEN_TARGET.md).

## Rules for the next change

1. Find the matching Svelte route and FastAPI router.
2. Put HTTP details in a router, business rules in a service, and SQL in a
   repository.
3. Add the narrowest test at the layer that owns the behavior.
4. Update this README only for durable architecture or operational changes;
   keep historical rationale in commits and pull requests.
