# B2 teacher-directory service/repository slice

## Summary

- Added `TeacherDirectoryRepository` for public teacher listing, filter
  options, count/pagination queries, public profile lookup, and index queries.
- Added `TeacherDirectoryService` for filter normalization, pagination rules,
  response assembly, compatibility messages, and public-profile serialization.
- Moved all teacher-directory SQL out of `backend/routers/teachers.py`; the
  router now maps HTTP inputs/results while preserving the existing factory
  signature.
- Preserved every teacher-directory route path, response model, status code,
  option message, and public/private field boundary.

## Verification

Commands run:

```bash
APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /opt/miniconda3/bin/pytest -q \
  tests/test_teacher_directory_service.py tests/test_teacher_directory_api.py \
  tests/test_backend_baseline_contracts.py
PATH=/opt/miniconda3/bin:/usr/local/bin:$PATH make test-static
```

Results:

- Focused teacher-directory and route-contract tests: 14 passed.
- Backend static suite: 176 passed.
- The last accumulated full parallel gate remains green at
  `.tmp/test-logs/20260711-003807/`; browser/integration suites were not
  rerun for this read-only directory extraction slice.

## Known issues

- The teacher-directory repository opens short-lived read sessions per query;
  the common request-scoped transaction convention remains a later B2 slice.
- No schema, migration, job, or legacy browser-route changes were made.

## Next best step

- Move on to identity/profile workflows, beginning with a read-only service
  boundary before mutation and provider integrations.
