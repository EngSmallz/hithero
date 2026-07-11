# Backend baseline contracts

Baseline captured 2026-07-10 before B1 package-boundary changes. This is the
B0 compatibility record for the FastAPI modular-monolith modernization.

## Baseline evidence

The canonical gate passed with the configured `/opt/miniconda3` runtime and
parallel suites:

```text
scripts/run-all-tests.sh
```

Log directory:
`.tmp/test-logs/20260710-212030/`

| Suite | Result |
| --- | --- |
| Python static tests | 164 passed |
| Frontend Playwright | 97 passed |
| Frontend integration | 16 passed |
| Legacy pytest E2E | 38 passed |

The interrupted pre-baseline attempts were environment/setup failures only:
the first shell did not expose `pytest`, the sandbox denied local test-server
binds, and interrupted browser runs left repository test servers on ports
8001/4173. The clean escalated run above passed after those stale processes
were stopped. No source changes were made during baseline execution.

## Route inventory

The route contract test in
`tests/test_backend_baseline_contracts.py` locks the business API/action
surface below. A route move or removal must update the test, this inventory,
and domain-specific contract coverage in one reviewed slice.

| Family | Routes | Current caller and contract coverage | Auth / legacy status |
| --- | --- | --- | --- |
| Internal jobs | `POST /internal/run-wednesday-job`, `/internal/run-tuesday-job`, `/internal/run-thursday-job`, `/internal/run-daily-job` | Platform scheduler or operator trigger; source inspection only in B0 | `x-secret-key` checked against `INTERNAL_JOB_SECRET`; daemon-thread jobs; private operational route |
| Public utility API | `GET /api/random_teacher/`, `POST /api/contact_us/` | SvelteKit home/contact flows; public teacher API status coverage in `tests/test_teacher_directory_api.py`; frontend integration covers contact path | Public; contact requires reCAPTCHA; API endpoints are authoritative and not legacy HTML |
| Public teacher legacy/API | `GET /spotlight/{token}`, `GET /teacher/{url_id}`, `GET /promo/get_promo_info/` | Retained legacy browser pages and public links; clean teacher route uses `/api/teacher/{url_id}/`; public-page and legacy E2E coverage | Public; legacy browser responsibility remains documented in `docs/route-status-matrix.md` |
| Directory options | `GET /api/get_states/`, `/api/get_counties/{state}`, `/api/get_districts/{state}/{county}`, `/api/get_schools/{state}/{county}/{district}` | Register/profile SvelteKit forms and legacy fallback pages; frontend route tests and static HTML contracts | Public; legacy-compatible JSON shapes including `{"message": ...}` for empty dependent lists |
| Directory index options | `GET /api/index_states/`, `/api/index_counties/{state}`, `/api/index_districts/{state}/{county}`, `/api/index_schools/{state}/{county}/{district}` | Retained index/legacy browser flows; route inventory only in B0 | Public; legacy-compatible endpoints |
| Teacher directory | `GET /api/teachers/`, `GET /api/teacher/{url_id}/`, `POST /api/index_teachers/` | SvelteKit `/teachers` and `/teacher/[urlId]`; `tests/test_teacher_directory_api.py`; frontend Playwright/integration | Public reads; index form endpoint public; response DTOs are existing compatibility contracts |
| Forum reads/writes | `POST /forum/create_post`, `GET /forum/get_posts`, `GET /forum/get_post`, `POST /forum/posts/{post_id}/vote`, `POST /forum/posts/{post_id}/comment`, `GET /forum/comments/{post_id}/`, `DELETE /forum/post/{post_id}/delete`, `DELETE /forum/comment/{comment_id}/delete`, `PATCH /forum/post/{post_id}/update`, `PATCH /forum/comment/{comment_id}/update` | SvelteKit forum routes; `tests/test_forum_formatting.py`, `tests/test_forum_session_cleanup.py`, frontend Playwright/integration | Reads public; mutations session-authenticated; sanitizer and rollback contracts already covered; legacy browser pages retained |
| Identity and profile | `POST /profile/register/`, `/profile/login/`, `/profile/logout/`, `/profile/create_teacher_profile/`, `GET /api/profile/`, `/api/get_teacher_info/`, `POST /profile/update_info/`, `/profile/update_teacher_school/`, `/profile/update_teacher_name/`, `/profile/update_wishlist/`, `/profile/update_url_id/`, `/profile/update_teacher_image/`, `GET /profile/myinfo/`, `POST /profile/update_password/`, `GET /api/check_access_teacher/`, `POST /profile/forgot_password/`, `/profile/reset_password/`, `GET /api/teacher_url/` | SvelteKit auth/profile flows, legacy fallback pages, frontend integration auth matrix, and static form contracts | Login/register/reset public; profile reads/writes session-sensitive; current session cookie is Starlette-managed; route compatibility retained |
| Moderation/admin | `POST /validation/validate_user/{user_email}`, `GET /api/validation_list/`, `POST /validation/delete_user/{user_email}`, `/validation/report_user/{user_email}`, `/validation/emailed_user/{user_email}`, `POST /admin/generate_teacher_report/`, `POST /profile/delete/` | SvelteKit validation/admin flows, legacy admin pages, frontend integration where applicable; direct negative API coverage is a B3 follow-up | Admin/role-sensitive; legacy browser routes retained until documented proof; current policy lives in router dependencies/helpers |

The application also exposes clean browser aliases and legacy/static browser
paths that are intentionally outside the business-route snapshot:

- Clean SvelteKit aliases: `/`, `/home`, `/about`, `/contact`, `/partners`,
  `/register`, `/login`, `/forgot`, `/update-password`, `/reset-password`,
  `/wishlist-setup`, `/terms`, `/teachers`, `/403`, `/404`, `/forum`,
  `/forum/new`, `/forum/post`, `/teacher`, `/validation`, `/admin`,
  `/profile/create`, and `/profile/edit`.
- Legacy/static paths: `/pages/*.html`, `/ads.txt`, `/sitemap.xml`, and the
  token-based legacy fallback `/{token}`. Every retained page has a disposition
  in `docs/route-status-matrix.md`; B0 does not remove or redirect any of them.

## Production assumptions and evidence gaps

These items are recorded as unknowns rather than inferred from source code:

- Supported SQL Server version, current production schema/constraints, row
  counts, data volumes, and backup/restore timings are not present in this
  repository. B4 requires a production-shaped schema/data review before
  migrations or constraints.
- Reverse-proxy routing, trusted proxy headers, HTTPS termination, and cookie
  rewriting must be confirmed against the deployed topology. The intended
  shape is documented in `docs/deployment-topology.md`, but it is not staging
  evidence.
- The scheduler trigger source and restart/overlap behavior are not verified
  outside the current authenticated HTTP triggers. B5 must replace the daemon
  thread execution model with a durable, observable mechanism.

## B0 exit criteria

- [x] Route surface is inventory-backed and protected by a contract snapshot.
- [x] Existing success, validation, auth, authorization, sanitization, and
  database-error coverage is linked for the domains already tested.
- [x] Full baseline gate passed with logs retained under `.tmp/test-logs/`.
- [x] Production assumptions are explicitly marked as evidence gaps.
- [x] No production schema, API response, or legacy browser route changed.

Next slice: B1 should introduce the application factory and package boundaries
behind this snapshot, beginning with settings/session/engine wiring while
leaving the compatibility `app.py` export intact.
