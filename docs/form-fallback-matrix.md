# Form Fallback Matrix

This table tracks migrated forms, their current native behavior, and the desired final fallback posture. It supports `ticket/P1-04-svelte-form-fallback-audit.md`.

| Route | Form/action | Fallback decision | Current behavior | Priority |
| --- | --- | --- | --- | --- |
| `/teachers` | `GET /teachers` | Native-safe GET. | Search/filter form posts to the Svelte route and remains crawlable enough for current needs. | P1 |
| `/contact` | `POST /contact` SvelteKit action | SvelteKit-owned fallback; no-JS cannot complete reCAPTCHA, so it renders a Svelte error instead of backend JSON. | Hydrated handler still appends reCAPTCHA and posts to FastAPI for in-page status. | P1 |
| `/register` | `POST /register` SvelteKit action | SvelteKit-owned fallback; no-JS cannot complete reCAPTCHA/dependent school selects, so it renders a Svelte error instead of backend JSON. | Hydrated handler preserves client validation, dependent selects, reCAPTCHA, and in-page status. | P1 |
| `/login` | `POST /login` SvelteKit action | SvelteKit-owned fallback; action proxies FastAPI login, forwards the session cookie, and redirects to the clean route on success. | Hydrated handler still routes by role/profile state without a full reload. | P1 |
| `/forgot` | `POST /forgot` SvelteKit action | SvelteKit-owned fallback; action proxies FastAPI and renders the safe reset-message on the Svelte page. | Hydrated handler still shows the returned status in place. | P1 |
| `/reset-password` | `POST /reset-password?...` SvelteKit action | SvelteKit-owned fallback; action validates mismatches locally, proxies FastAPI, and renders success/error on the Svelte page. | Hydrated handler still handles token/mismatch/status in place. | P1 |
| `/update-password` | `POST /update-password` SvelteKit action | SvelteKit-owned authenticated fallback; action forwards the session cookie to FastAPI and redirects to `/teacher` on success. | Hydrated handler still shows validation messages and redirects on success. | P1 |
| `/profile/create` | `POST /profile/create` SvelteKit action | SvelteKit-owned authenticated fallback; action forwards the session cookie and renders the clean success state. Dependent selects still need JS for normal completion. | Hydrated handler still loads dependent school choices and shows "View My Page". | P1 |
| `/profile/edit` | Named SvelteKit actions on `/profile/edit` | SvelteKit-owned authenticated fallback for each direct update form; actions forward the session cookie and redirect cleanly on success. | Hydrated handlers still show section status and return to `/teacher`. | P1 |
| `/forum/new` | `POST /forum/new` SvelteKit action | SvelteKit-owned authenticated fallback. | Hydrated handler redirects to `/forum/post?id=...`; no-JS fallback renders a clean success state and "Open Discussion" link. | P0 |
| `/forum/post` edit post | Client-only patch flow | Intentionally JavaScript-required app interaction. | Form has no backend `action`, so native submit does not expose raw JSON. Authenticated users get in-page failure status if fetch fails. | P1 |
| `/forum/post` add comment | Client-only form posts with fetch | Intentionally JavaScript-required app interaction. | Form has no backend `action`, so native submit does not expose raw JSON. Authenticated users get in-page failure status if fetch fails. | P1 |
| `/forum/post` edit comment | Client-only patch flow | Intentionally JavaScript-required app interaction. | Form has no backend `action`, so native submit does not expose raw JSON. Authenticated users get in-page failure status if fetch fails. | P1 |
| `/admin` teacher report | Client-only form posts with fetch | Intentionally JavaScript-required admin tool. | Form has no backend `action`, so native submit does not expose raw JSON. Admin users get in-page failure status if fetch fails. | P1 |
| `/admin` delete user | Client-only form posts with fetch and confirm | Intentionally JavaScript-required destructive admin tool. | Form has no backend `action`, so native submit does not expose raw JSON. Admin users get confirm + in-page failure status if fetch fails. | P1 |

## Audit Rule

Every form should be one of:

1. Native-safe without JavaScript.
2. SvelteKit action/proxy safe without JavaScript.
3. Explicitly JavaScript-required with graceful UX and documented rationale.

No form should dump users onto raw backend JSON.
