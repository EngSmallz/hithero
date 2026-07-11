# P1-08: Broaden Forum HTML Safety Contract

## Problem

Forum content now supports a small sanitized HTML subset and Svelte renders it with `{@html}`. That can be safe only if the backend sanitization contract is explicit, tested, and consistently applied to create, read, edit, list, detail, posts, titles, and comments.

## Scope

- Define the exact allowed tags and attributes.
- Ensure sanitization decodes repeatedly enough to prevent encoded bypasses.
- Sanitize legacy dirty DB rows on read.
- Sanitize create and edit flows.
- Ensure frontend rendering never receives unsanitized forum HTML.

## Acceptance Criteria

- Tests cover post title and content creation.
- Tests cover comment creation.
- Tests cover post and comment edits.
- Tests cover list and detail reads.
- Tests cover legacy dirty rows.
- Tests cover double-encoded payloads, malformed tags, unsafe protocols, event handlers, scripts, images, and unsafe attributes.
- Allowed links are safe and styled consistently.

## Verification

- `tests/test_forum_formatting.py`
- Frontend forum Playwright tests for rendered formatting.
- `make test-static`
- `npm --prefix frontend run test:e2e`
