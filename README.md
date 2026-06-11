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

Run the static and import regression tests with:

```bash
make test-static
```

Run the browser smoke tests with:

```bash
make test-e2e
```

The e2e tests start a local Uvicorn server on `127.0.0.1` by default. If your environment requires a different bind or browser URL host, override them with `E2E_BIND_HOST`, `E2E_CLIENT_HOST`, and optionally `E2E_PORT`.

Run the full regression baseline with:

```bash
make test
```

The test commands set `APP_ENV=test`, which imports the FastAPI app with an isolated SQLite database URL and skips automatic table creation. In test mode the app does not require the SQL Server `pyodbc` driver to be importable.

The Makefile also sets `PYTHONPATH=tests/stubs`. That path contains a test-only `readline` stub because the local Python 3.13 build used for this project segfaults when pytest imports the system readline extension during startup. The stub is not used by the application runtime.
