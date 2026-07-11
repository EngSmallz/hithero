# P1-04: Audit Every Svelte Form Fallback

## Problem

Several migrated Svelte routes use real forms with direct FastAPI `action` URLs and client-side submit handlers. That is good for semantics, but each form needs an intentional fallback story so users are not stranded on backend JSON, backend-only pages, or confusing redirects.

## Scope

Audit all Svelte forms, especially:

- `/contact`
- `/register`
- `/login`
- `/forgot`
- `/reset-password`
- `/update-password`
- `/profile/create`
- `/profile/edit`
- `/forum/new`
- `/forum/post` comment/edit actions
- `/admin`
- `/validation`

For each form, decide whether it should:

- Work without JavaScript via SvelteKit action/proxy.
- Work without JavaScript via backend redirect.
- Require JavaScript but display a graceful, explicit failure state.

## Acceptance Criteria

- Every migrated form has an intentional fallback decision.
- No form can leave users on raw backend JSON.
- No form posts users to a backend URL that lacks a clean browser-facing result.
- Tests cover the highest-risk forms.
- Any intentionally JavaScript-required form is documented with rationale.

## Verification

- Search all `action=` and `onsubmit=` usage in `frontend/src/routes`.
- Focused Playwright checks for critical form fallback behavior.
- `scripts/run-all-tests.sh`
