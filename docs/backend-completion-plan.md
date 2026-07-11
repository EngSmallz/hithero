# Backend Completion Plan

**Status: B0 complete; B1 application-factory slice in progress (2026-07-10).**

The baseline route inventory, contract snapshot, and full-gate evidence are
recorded in [`docs/backend-baseline-contracts.md`](backend-baseline-contracts.md)
and [`agent-reports/2026-07-10-b0-backend-baseline-contracts.md`](../agent-reports/2026-07-10-b0-backend-baseline-contracts.md).
No production schema or legacy browser route was changed in B0.

B1 progress is tracked in
[`agent-reports/2026-07-10-b1-application-factory.md`](../agent-reports/2026-07-10-b1-application-factory.md).
The compatibility `app.py` export remains authoritative while the remaining
database/model/router extraction slices are staged behind it.

The database/session boundary slice and its verification are recorded in
[`agent-reports/2026-07-10-b1-database-session-boundary.md`](../agent-reports/2026-07-10-b1-database-session-boundary.md).

The frontend migration is substantially implemented, but the FastAPI backend is
only partially modularized. `app.py` remains the composition root *and* holds
database models, infrastructure adapters, scheduled-job logic, shared auth
helpers, and a few endpoints. Existing routers are a useful first boundary,
not the finished target.

This document defines the work required to call the backend architecture
complete. It deliberately separates release blockers from structural cleanup;
the latter should not be disguised as already-complete work.

## Completion Definition

The backend is complete when it is a modular monolith with:

- a small application-composition module that only configures FastAPI and
  wires dependencies;
- domain routers that handle HTTP concerns only;
- explicit schemas, services, repositories/data access, jobs, and integration
  adapters in dedicated modules;
- database schema migrations and enforced integrity constraints;
- predictable authentication, authorization, validation, errors, transactions,
  observability, and operations; and
- no production browser path depending on legacy HTML served by FastAPI.

This does **not** mean microservices. One deployable FastAPI application and
one database remain the intended architecture.

## Workstreams

### B0 — Establish the baseline and preserve behavior

**Purpose:** prevent an architectural refactor from silently changing the
product.

Tasks:

1. Inventory every FastAPI endpoint, its caller, authentication requirement,
   request/response contract, legacy status, and test coverage.
2. Add focused API contract tests before moving each domain. Include success,
   validation, authentication, authorization, and database-error paths.
3. Record production configuration and data assumptions: SQL Server version,
   current schema, data volumes, proxy configuration, and scheduled-job
   trigger source.
4. Run the full gate on the baseline and retain its log location in the
   refactor handoff.

**Done when:** an endpoint can be moved only with a test proving its existing
contract, and production assumptions are not inferred from source code alone.

### B1 — Create the backend package boundaries

**Purpose:** make `app.py` a composition root rather than a second application
inside the application.

Target layout:

```text
backend/
  api/              # routers and HTTP dependencies
  db/               # engine/session factory, ORM models, migrations
  schemas/          # Pydantic request and response DTOs
  services/         # use-case/business workflows
  repositories/     # SQLAlchemy queries and persistence operations
  integrations/     # email, reCAPTCHA, X, file/type detection
  jobs/             # scheduled use cases and trigger adapters
  core/             # settings, logging, security, exceptions
  main.py           # create_app() and router/middleware wiring
```

Tasks:

1. Introduce an application factory, `create_app(settings)`, and move
   middleware, exception handlers, mounts, and router registration there.
2. Move SQLAlchemy engine/session construction to `backend/db` and expose a
   request-scoped session dependency.
3. Move ORM models out of `app.py`, without changing table names or columns.
4. Move Pydantic models to `backend/schemas`; use request and response models
   consistently.
5. Move shared auth/session dependencies and settings to `backend/core`.
6. Leave a temporary compatibility `app.py` that exports the ASGI `app`, then
   remove it only after all deployment commands use the new application entry
   point.

**Done when:** `app.py` is a thin compatibility entry point or removed, and no
domain behavior, model definition, job, or integration implementation lives in
the composition module.

### B2 — Finish domain-layer extraction

**Purpose:** routers should translate HTTP; services should own use cases;
repositories should own database access.

Tasks:

1. **Identity and profile:** extract registration, login, password reset,
   profile creation/editing, image upload, and URL-id allocation from
   `backend/routers/profile.py` into services and repositories.
2. **Teacher directory:** complete the existing extraction by moving queries
   and filter construction out of the router. Keep the public profile DTO free
   of private fields.
3. **Forum:** retain the sanitization boundary, but move post/comment/vote
   workflows and transaction logic into services. Define authorization policies
   for edit/delete explicitly and test them.
4. **Moderation/admin:** extract validation and district-scope policy into a
   service/policy object. Avoid duplicating role and scope checks across
   endpoints.
5. Replace manual `session_factory()`/`try/finally` repetitions with a common
   dependency and one transaction convention.
6. Replace broad `except Exception` response handling with typed domain errors
   mapped centrally to stable HTTP errors; always roll back failed mutations.

**Done when:** route functions contain parsing, dependency injection, a single
service call, and HTTP response mapping—not SQLAlchemy queries, business
decisions, or provider calls.

### B3 — Secure and normalize the API boundary

**Purpose:** remove accidental legacy behavior and make security guarantees
reviewable.

Tasks:

1. Define a single session/auth dependency model. Document cookie attributes,
   session fixation prevention at login, logout invalidation, CSRF protection
   for cookie-authenticated mutations, and trusted-proxy handling.
2. Use explicit response models for all public and mutation endpoints. Replace
   ambiguous `{\"message\": ...}` success/failure payloads with appropriate
   HTTP statuses and predictable error bodies.
3. Apply input validation at DTO boundaries: lengths, formats, pagination,
   URL allowlists, email normalization, and file-size/type checks.
4. Audit rate limits on login, registration, reset, contact, forum mutations,
   upload, and internal-job triggers. Ensure the limiter has a production-safe
   shared store if multiple backend processes run.
5. Audit authorization endpoint by endpoint, particularly profile ownership,
   forum ownership, teacher district scope, and admin functions. Add negative
   tests for each policy.
6. Move reCAPTCHA, Azure Email, and X calls behind provider interfaces;
   configure timeouts, retries where safe, and structured failure logging.
7. Keep the forum HTML allowlist explicit and tested before any output is
   rendered as HTML.

**Done when:** security and API contracts are enforced by reusable code and
tests, rather than route-by-route convention.

### B4 — Make the database production-managed

**Purpose:** eliminate schema drift and hidden data-integrity assumptions.

Tasks:

1. Introduce Alembic migrations from the current production SQL Server schema;
   do not rely on `Base.metadata.create_all()` in production.
2. Establish a safe migration rollout and backup/restore procedure; rehearse
   against a production-shaped copy before applying a destructive change.
3. Add appropriate database constraints and indexes after checking existing
   data: unique registered-user email, unique teacher URL ID, foreign keys,
   non-null requirements, forum vote uniqueness, password-reset token
   lifecycle, and directory query indexes.
4. Normalize model naming and map legacy column names without a broad,
   unnecessary schema rewrite.
5. Add repository integration tests that run against the supported production
   dialect as well as SQLite where behavior differs.

**Done when:** deploys apply versioned migrations, required data invariants are
enforced by the database, and schema changes are reviewable artifacts.

### B5 — Make jobs and integrations reliable

**Purpose:** scheduled emails and social posts must not depend on an arbitrary
web-process thread surviving.

Tasks:

1. Move daily/weekly job use cases out of `app.py` into `backend/jobs`.
2. Decide and document a durable execution model: a dedicated worker/queue,
   platform scheduler invoking a one-shot worker command, or another
   observable at-least-once mechanism. Do not keep daemon threads as the
   execution engine.
3. Add idempotency/locking so duplicate scheduler calls cannot send duplicate
   emails or publish duplicate teacher-of-the-day posts.
4. Keep authenticated trigger endpoints only if they are needed; otherwise
   remove them. Protect retained triggers with secret rotation, request
   authentication, audit logs, and rate limiting.
5. Add provider timeouts and failure handling. Record job run status, counts,
   errors, and retries in durable storage or the platform's job logs.
6. Make all external providers replaceable in tests without network access.

**Done when:** a web restart cannot silently abandon or duplicate a scheduled
task, and operations can answer whether a job ran and what it did.

### B6 — Retire the backend's browser/legacy responsibility

**Purpose:** complete the SvelteKit/FastAPI separation instead of maintaining
two page-serving systems indefinitely.

Tasks:

1. Complete the deferred SvelteKit authenticated-route proof documented in
   `docs/route-status-matrix.md`—especially form fallback, query preservation,
   role behavior, and noindex behavior.
2. Replace FastAPI page aliases and legacy error-page serving with redirects or
   SvelteKit-owned pages only when tests prove the behavior is preserved.
3. Remove `pages/` static serving, legacy HTML files, legacy error handlers,
   and compatibility APIs once their route matrix rows are marked removable.
4. Keep FastAPI focused on `/api/*`, explicit mutation/action endpoints,
   internal jobs, and static assets only where the deployment deliberately
   assigns them to FastAPI.
5. Update reverse-proxy rules so exact API/action paths take precedence over
   SvelteKit's browser-route fallback.

**Done when:** no production browser route is served by FastAPI as legacy HTML
and legacy files are no longer test dependencies.

### B7 — Operational readiness and release proof

**Purpose:** make the system supportable after the AI-driven implementation
phase ends.

Tasks:

1. Add `/healthz` (process liveness) and `/readyz` (database/dependency
   readiness), with no secrets or sensitive details in responses.
2. Add structured logs, request/correlation IDs, exception reporting, and
   metrics for latency, errors, database pool use, rate limits, emails, and
   jobs.
3. Configure production logging and secret management; ensure secrets never
   enter source, browser-visible variables, or logs.
4. Document local, staging, and production deployment/runbook procedures,
   rollback, migration rollback policy, backup/restore, and incident contacts.
5. Run a staging verification using the real reverse proxy, HTTPS, cookies,
   SQL Server, scheduled jobs, and third-party sandbox/provider configuration.
6. Run `scripts/run-all-tests.sh`, targeted security/authorization tests, and
   a manual production-like smoke checklist. Preserve results in a release
   report.

**Done when:** a new maintainer can deploy, diagnose, and roll back the system
without relying on undocumented knowledge.

## Recommended Order

1. B0 baseline and contracts.
2. B1 package boundaries and application factory.
3. B2 domain extraction, one domain at a time.
4. B3 security/API normalization alongside each domain move.
5. B4 migrations and constraints, with a dedicated data review.
6. B5 jobs/integrations.
7. B6 legacy retirement after browser proof.
8. B7 staging and release evidence.

Avoid a single large rewrite. Each workstream should be a small, reviewable
change with focused tests, then the canonical `scripts/run-all-tests.sh` gate.

## Explicit Non-Goals

- Do not split this into microservices merely to appear modern.
- Do not replace SQL Server or authentication as a side effect of code
  organization.
- Do not remove legacy pages before the documented route-specific proof exists.
- Do not claim completion from passing unit tests alone; deployment, schema,
  security, and job evidence are part of completion.
