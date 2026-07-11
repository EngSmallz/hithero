# Frontend modernization review fixes

## Summary

- Protected `/forum` and `/forum/post` with server-side role checks so anonymous requests redirect to `/login` before forum HTML or API reads occur.
- Added anonymous redirect coverage and updated authenticated forum route tests.
- Corrected Playwright action helpers to distinguish `APIResponse` from browser `Response`.
- Made frontend Python subprocesses use `PYTHON` when configured and otherwise fall back to `python3`; removed remaining bare `python` usage from the frontend test harness.
- Removed the private forum from the static public-page SEO suite and authenticated the real-stack forum read integration tests.

## Verification

- `npm --prefix frontend run check` — passed, 0 errors and 0 warnings.
- `npm --prefix frontend run lint` — passed.
- `npm --prefix frontend run test:e2e:forum` — passed, 19 tests.
- `npm --prefix frontend run test:e2e:public` — passed, 17 tests.
- `npm --prefix frontend run test:e2e:profile` — passed, 20 tests.
- `npm --prefix frontend run test:integration:one` — 14 tests passed; the two forum read tests initially failed because the integration fixtures had not logged in after the privacy change.
- Focused real-stack rerun for those two forum tests — passed, 2 tests.
- `scripts/run-all-tests.sh` — passed in the project's activated Conda `base` environment: Python static tests, frontend Playwright tests, frontend integration tests, and legacy pytest E2E tests all passed. The first Codex-run attempt used a non-activated shell that did not expose Conda's `python` or `pytest`; that was an execution-environment mismatch, not a repository dependency failure.

## Caveat

Codex command shells may not inherit the user's interactive Conda activation. Invoke commands through the Conda environment explicitly when the canonical gate requires its Python toolchain.
