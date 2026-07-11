# P1-09: Add Frontend Coverage For Teacher Directory Pagination

## Problem

Backend teacher-directory pagination is implemented and tested, but the Svelte `/teachers` pagination UX needs direct coverage.

## Scope

- Test rendered pagination controls.
- Test `page` query parameter behavior.
- Test filters combined with pagination.
- Test out-of-range pages.
- Test empty results and clear filters.

## Acceptance Criteria

- `/teachers?page=2` renders the expected page and page label.
- Previous/Next links preserve selected filters.
- Out-of-range page requests clamp or recover predictably.
- Empty result states remain clear.
- Backend total/page/page_size/total_pages metadata is represented correctly in the UI.

## Verification

- Add/update frontend Playwright tests for `/teachers`.
- Existing backend pagination tests still pass.
- `npm --prefix frontend run test:e2e`
- `make test-static`
