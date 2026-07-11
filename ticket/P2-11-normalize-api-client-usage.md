# P2-11: Normalize API Client Usage Across Svelte Routes

## Problem

Some Svelte routes use shared API helpers while others hand-roll `fetch`, credentials, JSON parsing, and error extraction. That increases the chance of inconsistent auth, CORS, and error UI behavior.

## Scope

- Inventory frontend API calls.
- Move repeated URL building, credentials, JSON parsing, and error handling into shared helpers where practical.
- Keep route-specific behavior readable.
- Avoid large abstraction churn where a one-off direct fetch is clearer.

## Acceptance Criteria

- Authenticated requests consistently send credentials.
- Error messages are extracted consistently from `detail` and `message`.
- Backend origin handling is centralized.
- No route loses existing behavior during normalization.
- Tests remain green.

## Verification

- Search `fetch(` in `frontend/src`.
- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e`
- `INTEGRATION_WORKERS=1 npm --prefix frontend run test:integration` or the canonical gate once P0-02 is complete.
