# Local Development

The incremental frontend migration runs SvelteKit and FastAPI side by side.

## Services

- FastAPI backend: `http://localhost:8000`
- SvelteKit frontend: `http://localhost:5173`

Run the backend:

```bash
make dev-backend
```

Run the frontend in another terminal:

```bash
make dev-frontend
```

The frontend reads `PUBLIC_BACKEND_ORIGIN`, defaulting to `http://localhost:8000`.
Routes that are not migrated yet can redirect to the backend during development.
Production topology, cookie/CORS expectations, and reverse-proxy assumptions are documented in `docs/deployment-topology.md`.

Local and test backend runs allow SvelteKit dev origins by default:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Override with `CORS_ALLOW_ORIGINS` when needed.

Session cookies are secure-only outside local/test environments. In
`APP_ENV=development`, the backend can be exercised over plain localhost HTTP.

## Local SQLite

For this Python/FastAPI stack, SQLite is the practical local and test database.
H2 is a Java database and would add JDBC/runtime complexity that does not match
the current SQLAlchemy setup.

`make dev-backend` defaults to:

```text
DATABASE_URL=sqlite:///./.local/hithero-dev.sqlite
```

To initialize a persistent test database:

```bash
make init-test-db
```

That target defaults to:

```text
TEST_DATABASE_URL=sqlite:///./.tmp/hithero-test.sqlite
```

The normal tests still use in-memory SQLite unless `TEST_DATABASE_URL` is set.
