# P1-05: Close Forum DB Sessions On All Error Paths

## Problem

Some forum endpoints open a database session and can raise before reaching a `finally` block. Examples include invalid vote input, missing post, or missing parent comment checks. Under real parallel traffic, leaked sessions and inconsistent rollback/close behavior can create subtle instability.

## Scope

- Review all endpoints in `backend/routers/forum.py`.
- Ensure sessions are closed for success and every exception path.
- Ensure failed mutations rollback before close where appropriate.
- Add tests for important 400, 401, 403, and 404 paths.

## Acceptance Criteria

- Every endpoint that creates a DB session closes it exactly once.
- Every mutation rolls back on failure before closing.
- Invalid vote type returns 400 without leaking a session.
- Missing post/comment paths return 404 without leaking a session.
- Unauthorized edit/delete paths return 403 without leaking a session.
- Tests cover the new error-path guarantees.

## Verification

- Focused backend tests for forum error paths.
- Existing forum formatting tests still pass.
- `make test-static`
