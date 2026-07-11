# Agent Guide

## Running Commands in Codex

Run commands from the repository root (`/Users/samuelmahan/workspace/hithero`)
unless a command explicitly targets another directory. Before changing files,
inspect the relevant source, tests, and current `git status`; preserve unrelated
worktree changes and never reset, checkout, or delete user changes without an
explicit request.

Codex commands run in a restricted workspace by default. Read-only inspection
and writes inside the workspace are normally allowed. Commands that need
network access, GUI/browser control outside the test harness, writes outside
the workspace, or an interactive user environment may require escalation. If a
command fails because a tool is not on the non-interactive `PATH`, retry it
through the user's login shell (for example, `/bin/zsh -lic '...'`) and request
escalated permission with a concise explanation. Do not conclude that a
dependency is missing until the configured Conda/runtime environment has been
checked.

Use `rg`/`rg --files` for searches. Use `apply_patch` for source and
documentation edits; do not write files with shell redirection or ad-hoc
scripts. Keep command output focused, avoid destructive commands, and do not
install packages or access external services unless the user has authorized it.

For Python checks in environments where the interactive Conda setup is not
loaded, use the repository's test environment settings explicitly:

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest ...
```

For frontend commands, use the repository-local npm installation through the
`frontend` prefix:

```bash
npm --prefix frontend run check
```

Run focused checks while iterating, then the canonical gate before claiming
completion. If the canonical gate fails, report the exact command, suite, log
path, and whether the failure reproduced in a focused rerun. Do not hide
backend concurrency problems by serializing the required parallel suites.

When a task changes modernization behavior, write a short dated report under
`agent-reports/` describing the change, verification, caveats, and next step.

Use this file to orient quickly before changing the Homeroom Heroes codebase.

## Project Shape

- Backend: FastAPI in `app.py` with routers under `backend/routers`.
- Frontend: SvelteKit + TypeScript under `frontend/`.
- Legacy browser pages still exist under `pages/` and are intentionally retained until redirect/removal decisions are proven by tests.
- Modernization tickets live under `ticket/`.
- Modernization plans live under `docs/`.

## Canonical Verification

Use the full gate before claiming modernization work is done:

```bash
scripts/run-all-tests.sh
```

For quick feedback:

```bash
scripts/run-all-tests.sh --quick
```

The full script intentionally runs the slow suites in parallel. Parallel E2E is a requirement; do not serialize browser tests merely to hide backend concurrency problems. If parallel runs are flaky, fix test data isolation, generated frontend state collisions, port allocation, or backend session handling.

## Focused Commands

Backend:

```bash
make test-static
make test-e2e
make test-forum-api
make test-teachers-api
```

Frontend:

```bash
npm --prefix frontend run check
npm --prefix frontend run lint
npm --prefix frontend run test:e2e
npm --prefix frontend run test:e2e:forum
npm --prefix frontend run test:e2e:auth
npm --prefix frontend run test:e2e:profile
npm --prefix frontend run test:e2e:public
npm --prefix frontend run test:integration
npm --prefix frontend run test:integration:one
```

Use focused commands while iterating, then the canonical gate before finalizing.

## High-Signal References

- Route ownership and status: `docs/route-status-matrix.md`
- Form fallback audit: `docs/form-fallback-matrix.md`
- Agent handoff template: `docs/agent-handoff-template.md`
- Test workflow: `docs/test-workflow.md`
- Modernization tickets: `ticket/README.md`

## Common Pitfalls

- Do not delete legacy pages or routes until clean replacements, redirects, sitemap decisions, and tests are in place.
- Do not treat direct FastAPI form `action` URLs as automatically safe. Some can strand users on raw JSON if JavaScript is slow or disabled.
- Keep public/indexable pages server-rendered with title, description, canonical URL, and Open Graph metadata.
- Keep private/auth/admin/forum pages out of the sitemap and use `noindex` where appropriate.
- Be careful running multiple SvelteKit dev/build processes outside the canonical test script; they may touch `.svelte-kit`.
- The Python tests set `PYTHONPATH=tests/stubs` to avoid a local Python 3.13 readline crash.
- Test mode uses SQLite and `APP_ENV=test`; production SQL Server/pyodbc should not be required for tests.

## Completion Standard

For modernization work, "done" means:

- Relevant ticket acceptance criteria are met.
- Focused tests for the changed area pass.
- `scripts/run-all-tests.sh` passes for merge/release confidence.
- A short, dense task report is written under `agent-reports/` using a dated slug, for example `agent-reports/2026-06-26-p1-04-form-fallback-audit.md`.
- Any known remaining issue is captured in `ticket/` or called out clearly in the task report.

Task reports should be brief but audit-ready: summarize what changed, why it changed, important implementation decisions, verification commands/results, known caveats, and the next best step. Use `docs/agent-handoff-template.md` as the shape when in doubt.
