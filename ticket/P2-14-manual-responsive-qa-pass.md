# P2-14: Complete Manual Responsive QA Pass

## Problem

Automated tests cover many behaviors, but the modernization also needs a deliberate human pass across mobile and desktop layouts. This catches visual overflow, awkward spacing, focus states, and workflow ergonomics that tests may miss.

## Scope

Review mobile and desktop for:

- Home
- About
- Contact
- Register/login/password flows
- Teacher directory
- Public teacher profile
- Profile create/edit
- Forum list/detail/new
- Validation
- Admin
- Error pages

## Acceptance Criteria

- Each route is checked at mobile and desktop widths.
- Main workflows are exercised.
- Keyboard focus states are spot-checked.
- Any layout, accessibility, or copy issues are captured as follow-up tickets.
- No text overlap or broken responsive controls remain in critical routes.

## Verification

- Manual checklist or screenshots.
- Browser pass at approximately 390px and 1280px widths.
- `npm --prefix frontend run test:e2e`
