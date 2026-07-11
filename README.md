Homeroom Heroes
Homeroom Heroes is a web application designed to help teachers get the supplies and support they need by connecting them with a supportive community. The platform features a daily "Teacher of the Day" to highlight a different educator each day and a spotlight on districts or counties once a week or month.

Features
Teacher of the Day: A random teacher is selected daily and featured on the homepage.

Teacher Profiles: Teachers can create and manage a profile to share their story and wishlist.

User Authentication: Secure login and registration for teachers.

District and County Spotlights: Weekly and monthly spotlights on schools and districts.

Testing
Install runtime and test dependencies, then install the Chromium browser used by Playwright:

```bash
make install-dev
```

Run the canonical modernization gate from the repository root before merge or release:

```bash
scripts/run-all-tests.sh
```

For faster local feedback while iterating, run:

```bash
scripts/run-all-tests.sh --quick
```

The full gate runs frontend format/check/lint first, prebuilds the SvelteKit app when both browser suites are selected, and then runs the slow suites in parallel. The legacy pytest browser smoke suite uses one internal worker inside that already-parallel gate by default; override `PYTEST_E2E_WORKERS` if you need to stress it directly. Logs for parallel suites are written to `.tmp/test-logs/<timestamp>/`.

Useful focused commands are still available while developing:

```bash
make test-static
make test-e2e
npm --prefix frontend run check
npm --prefix frontend run test:e2e:forum
npm --prefix frontend run test:integration
```

The legacy e2e tests start a local Uvicorn server on `127.0.0.1` by default. If your environment requires a different bind or browser URL host, override them with `E2E_BIND_HOST`, `E2E_CLIENT_HOST`, and optionally `E2E_PORT`.

The test commands set `APP_ENV=test`, which imports the FastAPI app with an isolated SQLite database URL and skips automatic table creation. In test mode the app does not require the SQL Server `pyodbc` driver to be importable.

The Makefile also sets `PYTHONPATH=tests/stubs`. That path contains a test-only `readline` stub because the local Python 3.13 build used for this project segfaults when pytest imports the system readline extension during startup. The stub is not used by the application runtime.

Deployment topology, required environment variables, cookie/CORS expectations, and reverse-proxy assumptions are documented in `docs/deployment-topology.md`.

For a manual SQLite-backed local test stack, including the test email and
reCAPTCHA behavior, see [local-test-README.md](local-test-README.md).
