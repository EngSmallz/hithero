# P1-10: Add No-JS Or Slow-JS Coverage For Critical Flows

## Problem

Modernized pages are server-rendered, but many workflows depend on hydration for interactive behavior. Critical paths should be resilient to slow JavaScript attachment or should fail gracefully without user data loss.

## Scope

Cover highest-risk flows:

- Login
- Register
- Contact
- Forgot password
- Reset password
- Update password
- Profile create/edit
- Forum create/comment/vote
- Admin actions

## Acceptance Criteria

- Critical forms do not silently fail when JavaScript is slow.
- No flow strands users on raw backend JSON.
- No user-entered data is lost without a clear error or recovery path.
- JavaScript-required flows are explicitly identified and handled gracefully.
- Tests simulate slow hydration or disabled JavaScript for the highest-risk routes.

## Verification

- Focused Playwright tests using JavaScript-disabled contexts where practical.
- Focused Playwright tests that submit immediately after `domcontentloaded`.
- `scripts/run-all-tests.sh`
