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

## Prepare an isolated SQLite database

Use a database file dedicated to this manual stack. Do not point it at the
database used by another test process or a production/local development
instance.

```bash
mkdir -p .tmp
APP_ENV=test \
SECRET_KEY=test-secret \
TEST_DATABASE_URL=sqlite:///./.tmp/local-test.sqlite \
make init-test-db
```

`init-test-db` creates the SQLAlchemy tables. It does not seed teachers,
schools, or users; create test records through the registration flow or seed
the SQLite file with a one-off fixture/script kept outside production code.

## Start the backend

In terminal 1:

```bash
APP_ENV=test \
SECRET_KEY=test-secret \
TEST_DATABASE_URL=sqlite:///./.tmp/local-test.sqlite \
TEST_RECAPTCHA_TOKEN=hithero-test-recaptcha \
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

The backend uses the SQLite URL selected by `TEST_DATABASE_URL` when
`APP_ENV=test`. It accepts local frontend origins and does not require the
SQL Server `pyodbc` driver.

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
