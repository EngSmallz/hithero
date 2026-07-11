# Deployment Topology

This document captures the intended SvelteKit + FastAPI deployment model for Homeroom Heroes after the frontend modernization.

## Intended Shape

Production should run SvelteKit and FastAPI behind one public HTTPS origin:

```text
https://www.helpteachers.net
  /, /teachers, /profile/*, /forum/*, ...
    -> SvelteKit server
  /api/*, /profile/* action APIs, /forum/* APIs, /admin/*, /validation/*, /spotlight/*, /promo/*
    -> FastAPI
  /static/*, /robots.txt, /sitemap.xml
    -> static asset owner, preferably the reverse proxy or FastAPI static mount
```

Separate frontend and backend processes are fine, but the public browser experience should be same-site. Same-site hosting keeps session cookies reliable and minimizes CORS exposure. If the services are hosted on separate internal origins, put a reverse proxy in front of them and route by path.

## Local Development

Local development intentionally runs the services side by side:

```bash
make dev-backend
make dev-frontend
```

Defaults:

```text
FastAPI:    http://localhost:8000
SvelteKit:  http://localhost:5173
```

The frontend reads `PUBLIC_BACKEND_ORIGIN` and defaults to `http://localhost:8000`. Override it only when the browser must call a different backend origin.

## Required Environment Variables

Safe local examples:

```text
APP_ENV=development
SECRET_KEY=dev-secret
DATABASE_URL=sqlite:///./.local/hithero-dev.sqlite
PUBLIC_BACKEND_ORIGIN=http://localhost:8000
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Production examples:

```text
APP_ENV=production
SECRET_KEY=<strong random secret>
DATABASE_URL=<production SQLAlchemy database URL>
PUBLIC_BACKEND_ORIGIN=https://www.helpteachers.net
CORS_ALLOW_ORIGINS=https://www.helpteachers.net,https://helpteachers.net
SERVER_KEY_CAPTCHA=<server reCAPTCHA secret>
```

Test-only examples:

```text
APP_ENV=test
SECRET_KEY=test-secret
TEST_DATABASE_URL=sqlite:///./.tmp/hithero-test.sqlite
PUBLIC_BACKEND_ORIGIN=http://localhost:8001
```

Notes:

- `DATABASE_URL` wins when set. Otherwise `APP_ENV=test` uses `TEST_DATABASE_URL` or in-memory SQLite, and local development uses `LOCAL_DATABASE_URL` or `.local/hithero-dev.sqlite`.
- `SECRET_KEY` is required for signed session cookies. Use a stable, strong secret in production so sessions survive process restarts.
- `PUBLIC_BACKEND_ORIGIN` is exposed to browser code. Do not put secrets in it.

## Cookies And CORS

FastAPI uses Starlette session cookies. Cookie transport is controlled by `APP_ENV`:

- `APP_ENV=development`, `dev`, `local`, or `test`: cookies are allowed over local HTTP.
- Other environments: cookies are secure-only and require HTTPS.

CORS allows credentials. Production defaults are:

```text
https://www.helpteachers.net
https://helpteachers.net
```

Local/test environments also allow the SvelteKit dev origins on ports `5173` and `5174`. Use `CORS_ALLOW_ORIGINS` for explicit comma-separated origins when a deployment or test run uses different hosts or ports.

## Reverse Proxy Expectations

The reverse proxy should:

- Terminate HTTPS and forward `X-Forwarded-*` headers to both services.
- Route browser pages to SvelteKit.
- Route FastAPI API paths to the backend.
- Preserve cookies and request bodies for form posts and uploads.
- Serve or proxy `/static/*`, `/robots.txt`, and `/sitemap.xml` consistently.
- Avoid caching authenticated, admin, validation, profile, and forum responses.
- Allow larger request bodies for teacher image uploads up to the backend limit.

Path routing must be explicit because some browser routes and API routes share prefixes, especially `/profile/*` and `/forum/*`. Prefer routing exact known API endpoints before the broader SvelteKit route fallback.

## Static Assets And SEO Files

FastAPI currently mounts `static/` at `/static`. The deployment may serve those files directly from the proxy or proxy them to FastAPI, but the canonical files are in this repository:

- `static/robots.txt`
- `static/sitemap.xml`
- `static/images/*`
- `static/email_template.html`

The public sitemap and robots policy are tested by `tests/test_static_html_contracts.py` and frontend public-page E2E tests. Route ownership and indexing policy live in `docs/route-status-matrix.md`.

## Health Checks

There is no dedicated `/healthz` endpoint yet. Until one exists, use lightweight HTTP probes that exercise each service:

```text
SvelteKit page probe:  GET /
FastAPI data probe:   GET /api/teachers/?page=1&page_size=1
Static file probe:    GET /static/robots.txt
```

Add a dedicated backend health endpoint before relying on database-aware production liveness checks.

## Verification Gate

Use the canonical gate before merge or release:

```bash
scripts/run-all-tests.sh
```

For local iteration:

```bash
scripts/run-all-tests.sh --quick
```

Detailed test workflow notes live in `docs/test-workflow.md`.
