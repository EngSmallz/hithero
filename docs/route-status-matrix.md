# Route Status Matrix

This table is an agent-facing map of current browser route ownership, legacy mapping, indexing policy, and primary coverage. It is intentionally compact; update it when route ownership or cleanup status changes.

| Browser route | Svelte route | Legacy page/API alias | Auth/indexing policy | Primary backend/API dependencies | Primary tests |
| --- | --- | --- | --- | --- | --- |
| `/` | `frontend/src/routes/+page.svelte` | `pages/homepage.html` | Public, indexable | `/spotlight/teacher`, `/promo/get_promo_info/`, `/api/random_teacher/` | `frontend/src/routes/public-pages.e2e.ts`, `frontend/src/routes/homepage-actions.e2e.ts` |
| `/teachers` | `frontend/src/routes/teachers/+page.svelte`, `+page.server.ts` | `pages/index.html` | Public, indexable | `/api/teachers/` | `tests/test_teacher_directory_api.py`, `frontend/src/routes/public-pages.e2e.ts` |
| `/teacher/[urlId]` | `frontend/src/routes/teacher/[urlId]/+page.svelte`, `+page.server.ts` | `/teacher/{url_id}` redirect/session bridge | Public, indexable dynamic profile; not in static sitemap until dynamic sitemap generation exists | `/api/teacher/{url_id}/` | `frontend/tests/integration/auth.integration.ts` |
| `/teacher` | `frontend/src/routes/teacher/+page.svelte` | `pages/teacher.html` | Session/current-teacher route, noindex, not sitemap | `/api/get_teacher_info/`, `/profile/myinfo/`, profile image APIs | `frontend/src/routes/teacher/page.svelte.e2e.ts` |
| `/about` | `frontend/src/routes/about/+page.svelte` | `pages/about.html` | Public, indexable | Static content | `frontend/src/routes/about/page.svelte.e2e.ts`, `frontend/src/routes/public-pages.e2e.ts` |
| `/contact` | `frontend/src/routes/contact/+page.svelte` | `pages/contact.html` | Public, indexable | `/contact_us/`, reCAPTCHA | `frontend/src/routes/public-pages.e2e.ts` |
| `/partners` | `frontend/src/routes/partners/+page.svelte` | `pages/partners.html` | Public, indexable | Static content/assets | `frontend/src/routes/public-pages.e2e.ts` |
| `/terms` | `frontend/src/routes/terms/+page.svelte` | `pages/terms_conditions.html` | Public, indexable | Static content | `frontend/src/routes/public-pages.e2e.ts` |
| `/wishlist-setup` | `frontend/src/routes/wishlist-setup/+page.svelte` | `pages/wishlist_setup.html` | Public, indexable | Static content/assets | `frontend/src/routes/public-pages.e2e.ts` |
| `/login` | `frontend/src/routes/login/+page.svelte` | `pages/login.html` | Public, indexable | `/profile/login/` | `frontend/src/routes/login/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/register` | `frontend/src/routes/register/+page.svelte`, `+page.server.ts` | `pages/register.html` | Public, indexable | `/profile/register/`, school option APIs, reCAPTCHA | `frontend/src/routes/register/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/forgot` | `frontend/src/routes/forgot/+page.svelte` | `pages/forgot.html` | Public, indexable | `/profile/forgot_password/` | `frontend/src/routes/forgot/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/reset-password` | `frontend/src/routes/reset-password/+page.svelte` | `pages/reset_password.html` | Public entry, noindex | `/profile/reset_password/` | `frontend/src/routes/reset-password/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/update-password` | `frontend/src/routes/update-password/+page.svelte`, `+page.server.ts` | `pages/update_password.html` | Authenticated, noindex | `/profile/update_password/` | `frontend/src/routes/update-password/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/profile/create` | `frontend/src/routes/profile/create/+page.svelte`, `+page.server.ts` | `pages/create.html` | Authenticated, noindex | `/profile/create_teacher_profile/`, school option APIs | `frontend/src/routes/profile/create/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/profile/edit` | `frontend/src/routes/profile/edit/+page.svelte`, `+page.server.ts` | `pages/edit_teacher.html` | Authenticated, noindex | `/profile/myinfo/`, `/api/get_teacher_info/`, profile update APIs | `frontend/src/routes/profile/edit/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/forum` | `frontend/src/routes/forum/+page.svelte` | `pages/forum.html` | Auth/app route, noindex | `/forum/get_posts` | `frontend/src/routes/forum/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/forum/new` | `frontend/src/routes/forum/new/+page.svelte`, `+page.server.ts` | `pages/create_post.html` | Authenticated, noindex | `/forum/create_post` | `frontend/src/routes/forum/new/page.svelte.e2e.ts` |
| `/forum/post` | `frontend/src/routes/forum/post/+page.svelte` | `pages/post.html` | Auth/app route, noindex | `/forum/get_post`, `/forum/comments/{id}/`, vote/comment/edit/delete APIs | `frontend/src/routes/forum/post/page.svelte.e2e.ts`, `frontend/tests/integration/auth.integration.ts` |
| `/validation` | `frontend/src/routes/validation/+page.svelte`, `+page.server.ts` | `pages/validation.html` | Teacher/admin, noindex | `/api/validation_list/`, validation action APIs | `frontend/src/routes/validation/page.svelte.e2e.ts` |
| `/admin` | `frontend/src/routes/admin/+page.svelte`, `+page.server.ts` | `pages/admin.html` | Admin, noindex | report/delete/admin APIs, school option APIs | `frontend/src/routes/admin/page.svelte.e2e.ts` |
| `/403` | `frontend/src/routes/403/+page.server.ts` | `pages/403.html` | Error page, noindex in Svelte error flow | Static/error handling | `tests/test_clean_routes.py`, public legacy E2E |
| `/404` | `frontend/src/routes/404/+page.server.ts` | `pages/404.html` | Error page, noindex in Svelte error flow | Static/error handling | `tests/test_clean_routes.py`, public legacy E2E |

## Legacy Cleanup Notes

- Clean public legacy pages redirect via `backend/routers/legacy.py`.
- Session-sensitive, token-sensitive, or private legacy pages are still direct-served until the specific replacement proof below is complete.
- Do not delete a legacy HTML file until its row says redirect now and tests cover both GET and HEAD redirects.

## Legacy Page Disposition

| Legacy page | Clean route | Decision | Reason / removal proof |
| --- | --- | --- | --- |
| `pages/homepage.html` | `/` | Redirect now | Public Svelte route is canonical and covered by clean route, redirect, sitemap, and public browser tests. Remove after full release confidence on canonical route only. |
| `pages/index.html` | `/teachers` | Redirect now | Public teacher directory route is canonical and API-backed. Remove after full release confidence on canonical route only. |
| `pages/about.html` | `/about` | Redirect now | Public static Svelte route is canonical and covered by public tests. Remove after full release confidence on canonical route only. |
| `pages/contact.html` | `/contact` | Redirect now | Public Svelte route owns the contact form fallback and canonical URL. Remove after full release confidence on canonical route only. |
| `pages/partners.html` | `/partners` | Redirect now | Public static Svelte route is canonical and covered by public tests. Remove after full release confidence on canonical route only. |
| `pages/register.html` | `/register` | Redirect now | Public Svelte route owns registration and no-JS fallback. Remove after registration fallback and integration coverage remain green. |
| `pages/login.html` | `/login` | Redirect now | Public Svelte route owns login and redirect handling. Remove after auth integration coverage remains green. |
| `pages/forgot.html` | `/forgot` | Redirect now | Public Svelte route owns password-request fallback. Remove after auth integration coverage remains green. |
| `pages/terms_conditions.html` | `/terms` | Redirect now | Public static Svelte route is canonical and included in sitemap policy. Remove after full release confidence on canonical route only. |
| `pages/wishlist_setup.html` | `/wishlist-setup` | Redirect now | Public static Svelte route is canonical and included in sitemap policy. Remove after full release confidence on canonical route only. |
| `pages/403.html` | `/403` | Redirect now | Clean error route exists and legacy redirect is covered for GET and HEAD. Remove after backend error handlers no longer depend on the static file. |
| `pages/404.html` | `/404` | Redirect now | Clean error route exists and legacy redirect is covered for GET and HEAD. Remove after backend error handlers no longer depend on the static file. |
| `pages/reset_password.html` | `/reset-password` | Keep temporarily | Token-sensitive password reset entry. Keep until clean Svelte route has explicit legacy URL redirect tests preserving reset-token query behavior and no-JS fallback coverage. |
| `pages/update_password.html` | `/update-password` | Keep temporarily | Authenticated password change flow. Keep until auth/session fallback behavior is proven through SvelteKit-only no-JS and integration coverage. |
| `pages/forum.html` | `/forum` | Keep temporarily | Authenticated forum app route. Keep until forum list loading, empty/error states, and auth/noindex behavior are locked on the Svelte route. |
| `pages/create_post.html` | `/forum/new` | Keep temporarily | Authenticated forum create flow. Keep until progressive create fallback and auth redirect coverage are promoted into the full gate. |
| `pages/post.html` | `/forum/post` | Keep temporarily | Query-dependent forum detail route. Keep until legacy redirect can preserve `id` query semantics and comment/vote/edit/delete flows are fully covered. |
| `pages/teacher.html` | `/teacher` | Keep temporarily | Session/current-teacher bridge. Keep until current-user teacher route behavior is proven without static fallback. |
| `pages/create.html` | `/profile/create` | Keep temporarily | Authenticated profile create flow. Keep until SvelteKit actions and school dropdown fallback coverage are promoted into the full gate. |
| `pages/edit_teacher.html` | `/profile/edit` | Keep temporarily | Authenticated profile edit flow with multiple forms and image actions. Keep until SvelteKit-only fallback coverage proves all sections. |
| `pages/validation.html` | `/validation` | Keep temporarily | Teacher/admin-only workflow. Keep until role-gated Svelte route and validation mutations are fully covered. |
| `pages/admin.html` | `/admin` | Keep temporarily | Admin-only workflow. Keep until role-gated Svelte route and admin mutations are fully covered. |

## SEO And Indexing Policy

- Static public canonical routes in the sitemap: `/`, `/teachers`, `/about`, `/contact`, `/partners`, `/register`, `/login`, `/forgot`, `/terms`, `/wishlist-setup`.
- Public but token-sensitive route excluded from sitemap and rendered noindex: `/reset-password`.
- Dynamic public teacher profiles use canonical `/teacher/[urlId]` pages, but the current static sitemap does not enumerate data-driven teacher URLs.
- Private, authenticated, admin, validation, forum, current-teacher, and error routes are excluded from sitemap and render `noindex, nofollow` when browser HTML can exist.
- Forum list/detail/create remain private/noindex. Revisit only with a dedicated product and moderation decision about public forum indexing.
