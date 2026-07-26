# Local SQLite test stack

This guide runs FastAPI and SvelteKit locally without SQL Server. It uses a
SQLite file under `.tmp/`, keeps external email delivery disabled, and uses the
deterministic test reCAPTCHA token.

## Prerequisites

Install the Python and browser dependencies once:

```bash
make install-dev
```

The backend commands require Python, and the frontend commands require Node.js
and npm. In Codex, if those tools are not on the non-interactive `PATH`, run
the commands through the configured login shell as described in `AGENTS.md`.

## Start the backend

In terminal 1, run:

```bash
make local-test
```

For the normal full local development stack instead, use `make local`; it
delegates to the managed launcher and starts both FastAPI and SvelteKit.

Before FastAPI starts, `make local-test` creates the configured SQLite schema
with SQLAlchemy metadata and seeds 100 deterministic demo schools plus 50
public demo teacher profiles. The bootstrap is idempotent: a second run adds
zero rows. It never applies Alembic migrations and refuses non-SQLite URLs.
The checked-in source fixtures are
`scripts/fixtures/schools.csv` and
`scripts/fixtures/fake-public-teachers.csv`; they contain only obvious demo
values and no credentials or personal data.
The target explicitly clears `DATABASE_URL`, so it cannot accidentally use the
production/development database. Override `LOCAL_TEST_DATABASE_URL`,
`LOCAL_TEST_HOST`, or `LOCAL_TEST_PORT` when you need a separate instance.

The backend accepts local frontend origins and does not require the SQL Server
`pyodbc` driver.

Check that it is responding with a read-only endpoint:

```bash
curl -i http://127.0.0.1:8000/api/get_states/
```

## Start the frontend

In terminal 2:

```bash
PUBLIC_BACKEND_ORIGIN=http://127.0.0.1:8000 \
npm --prefix frontend run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173>. The backend CORS defaults include both
`http://localhost:5173` and `http://127.0.0.1:5173` in test mode.

## Downstream services are deliberately local-safe

With `APP_ENV=test`, the backend deliberately avoids real downstream calls:

- `send_email` and attachment email functions print a skip message and return
  success; Azure Communication Services credentials are not needed.
- reCAPTCHA accepts only `TEST_RECAPTCHA_TOKEN` (default:
  `hithero-test-recaptcha`). Use that value in registration and contact forms.
- X/Twitter posting is skipped when its credentials are absent.

This is the current application-level mock boundary: tests exercise the route
and database behavior while the email/reCAPTCHA providers remain deterministic
and offline. Do not put real Azure, reCAPTCHA, or X credentials in `.env.test`
or commit them. If a test needs to assert an outbound payload, inject or
monkeypatch the existing `send_email`, `send_attachment`, or
`verify_recaptcha` callable at the router boundary instead of contacting the
provider.

## Run tests against isolated databases

For the normal suite, prefer the repository commands because they set the
required test environment and parallel-worker isolation:

```bash
scripts/run-all-tests.sh --quick
scripts/run-all-tests.sh
```

Focused backend checks:

```bash
make test-forum-api
make test-teachers-api
make test-static
```

The full gate runs slow suites in parallel. Never run those suites against
`.tmp/local-test.sqlite`; use the default in-memory database or a unique
worker-specific `TEST_DATABASE_URL` instead. To remove only this manual stack,
stop the local processes and delete `.tmp/local-test.sqlite` when it is no
longer needed.

`make local` performs the same SQLite bootstrap for `LOCAL_DATABASE_URL`
(default `.local/hithero-dev.sqlite`) before handing control to the managed
launcher. The launcher remains responsible for starting and stopping servers.

## Common configuration mistakes

- `DATABASE_URL` takes precedence over `TEST_DATABASE_URL`; unset it when you
  intend to use the test SQLite file.
- `APP_ENV=development` selects the local-development behavior and does not
  guarantee downstream email suppression. Use `APP_ENV=test` for offline
  manual testing.
- A missing `SECRET_KEY` invalidates session behavior. Always set a local-only
  value such as `test-secret` or a generated development secret.
- If the browser cannot reach the backend, confirm both services use the same
  host spelling (`localhost` versus `127.0.0.1`) and that the matching CORS
  origin is configured.
