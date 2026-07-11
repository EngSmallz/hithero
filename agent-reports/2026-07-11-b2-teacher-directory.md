# B2 teacher-directory service/repository slice

## Summary

- Added `TeacherDirectoryRepository` for public teacher listing, filter
  options, count/pagination queries, and public profile lookup.
- Added `TeacherDirectoryService` for filter normalization, pagination rules,
  response assembly, and public-profile serialization.
- Updated only `/api/teachers/` and `/api/teacher/{url_id}/`; all route paths,
  response models, status codes, and public/private field boundaries remain
  compatible.
- Left the legacy option and `/api/index_teachers/` query handlers in the
  router for a later, separately tested slice.

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

- Focused teacher-directory and route-contract tests: 12 passed.
- Backend static suite: 174 passed.
- The last accumulated full parallel gate remains green at
  `.tmp/test-logs/20260711-003807/`; browser/integration suites were not
  rerun for this read-only directory extraction slice.

## Known issues

- The router still owns the legacy school/index option queries and
  `/api/index_teachers/`; those remain intentionally unchanged.
- No schema, migration, job, or legacy browser-route changes were made.

## Next best step

- Extract the remaining teacher-directory option/index queries behind the same
  repository/service boundary, with focused compatibility tests before moving
  on to identity/profile workflows.
