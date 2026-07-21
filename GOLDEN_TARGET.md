# Golden target

## Outcome

Run Homeroom Heroes as a compact SvelteKit/FastAPI application with the
SvelteKit UI as the only page layer, a documented compatibility API where it
is still needed, and no historical modernization tracking artifacts.

## Current baseline

- SvelteKit owns the intended user-facing routes and server-rendered public
  content.
- FastAPI is composed in `backend/main.py`; route wiring is centralized in
  `backend/api/composition.py`.
- SvelteKit is the only page implementation. `backend/routers/site.py` owns
  public site APIs, while `backend/routers/redirects.py` temporarily preserves
  old `/pages/*.html` links without keeping their HTML or browser scripts.

## Finish line

1. **Retire redirects deliberately.** The page layer is gone. Keep the small
   `/pages/*.html` redirect map only while externally published old URLs need
   it; remove it with the deployment routing decision.
2. **Delete compatibility code by callers, not by name.** Inventory each
   route in `backend/routers/site.py` and `backend/routers/compatibility.py`.
   Remove it only after the SvelteKit client and external integrations have no
   consumer, with focused route-contract coverage updated in the same change.
3. **Remove dead code and duplicate tests.** Use imports, route registration,
   production callers, and a passing focused test as evidence. Preserve tests
   that defend an API contract or a security boundary, even if they overlap at
   another layer.
4. **Tighten only demonstrated rough edges.** Favor small fixes to failures,
   authorization, transactions, accessibility, and deployment behavior over
   new abstractions or speculative infrastructure.

## Manual acceptance gate

Manual confirmation complements automated tests; it does not replace them.
Run this once against a disposable local dataset with an anonymous browser,
one teacher account, one administrator account, and a known public teacher
URL ID. Do not delete or modify real user data while testing.

| Area | Exercise | Pass condition |
| --- | --- | --- |
| Public pages | Visit `/`, `/about`, `/contact`, `/partners`, `/terms`, and `/wishlist-setup`. | Each has its expected content, title, navigation/footer, and no raw API response. |
| Directory and profiles | Search/filter `/teachers`, use pagination if available, open `/teacher/<known-id>`, and visit `/teacher` while signed in as that teacher. | Results, profile data, and session-specific profile behavior are correct. |
| Authentication | Register a disposable account, log in/out, follow a protected-route return redirect, and exercise forgot/reset-password with a valid test token. | Validation is clear; login state and return URL work; no form lands on raw backend JSON. |
| Profile mutations | Create or edit a disposable teacher profile, including dependent school selection, wishlist, image, and school-change request where available. | Saved data survives reload; validation and failure messages are understandable. |
| Forum | As a teacher, list/sort discussions, create a post, open it by `?id=`, add a comment, vote, edit, and delete only disposable content. | The right content changes, authorization is respected, and the query-selected post loads. |
| Authorization | As anonymous, teacher, and admin users, visit `/forum`, `/profile/create`, `/profile/edit`, `/validation`, and `/admin`. | Anonymous users are sent to login as appropriate; teachers cannot use admin/validation actions; admin workflows work on disposable records. |
| Errors and recovery | Visit an unknown URL, `/403`, `/404`, and submit one invalid form in each form family. | Correct 403/404 or inline validation appears; no stack trace or sensitive detail is exposed. |
| Legacy migration | Manually open `/pages/login.html?redirect=%2Fadmin`, `/pages/reset_password.html?token=test-token`, and `/pages/post.html?id=<known-post-id>`. | Each redirects to the clean SvelteKit URL and preserves its query string. |
| Small-screen smoke test | Repeat homepage navigation, login, one profile form, and one forum action at a narrow mobile viewport. | No blocked controls, horizontal overflow, or unreadable/hidden error state. |

Before authorizing page retirement, confirm every row above and record any
failure in the active task conversation. Then run the automated gate below.

## Completion proof

Each retirement slice must keep its focused backend/frontend checks green and
finish with:

```bash
scripts/run-all-tests.sh
```

Record durable operational or architectural changes by updating `README.md`.
Use commit messages and pull requests for historical rationale; do not revive
separate report, ticket, or planning directories.
