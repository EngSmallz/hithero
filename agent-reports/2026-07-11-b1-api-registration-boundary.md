# B1 API registration boundary — 2026-07-11

## Status

Focused/static verification passed and the slice is committed as a coherent
B1 composition milestone. The browser-inclusive canonical gate remains
pending for the accumulated B1 changes and is not claimed by this report.

## Changes

- Added `backend/api/register.py` with dependency-driven registration of the
  existing legacy, teacher, forum, profile, and admin routers.
- Preserved registration order, `/pages` mounting, legacy error handlers,
  router arguments, response models, and API paths.
- Replaced the large `app.py` registration block with one call to
  `register_routers(...)`; endpoint implementations remain in their existing
  routers and application compatibility names remain unchanged.
- Added the `backend/api` package boundary.

## Safety boundaries

No endpoint implementation, route, response shape, model, schema, production
table, or legacy browser path changed. This is composition-only extraction for
the modular monolith; FastAPI remains authoritative.

## Verification

Focused command:

```text
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /opt/miniconda3/bin/pytest tests/test_backend_baseline_contracts.py \
  tests/test_app_factory.py tests/test_model_schema_boundaries.py \
  tests/test_database_session_boundary.py tests/test_clean_routes.py -q
```

Result: 12 passed.

Fast backend/static gate:

```text
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

Result: 169 passed in 28.21 seconds.

## Next step

Run the accumulated browser-inclusive gate with the explicit combined PATH:

```text
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH scripts/run-all-tests.sh
```

Then continue B1 core/security boundary extraction or begin B2 domain services
with one domain at a time. Do not remove the compatibility `app.py` entry
point until deployment commands and tests use the new composition entry point.
