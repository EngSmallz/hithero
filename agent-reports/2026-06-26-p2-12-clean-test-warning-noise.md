# P2-12 Clean Test Warning Noise

## Summary

- What changed: Removed the Python deprecation warnings that appeared in the static test gate by updating SQLAlchemy and Pydantic usage at the source.
- Why it changed: P2-12 requires normal test output to stay warning-clean so new warnings are visible instead of buried in expected noise.
- Ticket(s): `ticket/P2-12-clean-test-warning-noise.md`

## Files Touched

- `app.py`

## Implementation Notes

- Replaced `sqlalchemy.ext.declarative.declarative_base` with `sqlalchemy.orm.declarative_base`.
- Replaced the Pydantic class-based `Config` on `PostDisplay` with `ConfigDict(from_attributes=True)`.
- No warning filters were added.

## Verification

Commands run:

```bash
make test-static
make test-e2e
scripts/run-all-tests.sh --quick
rg -n "Warning|Deprecation|deprecated|warnings.warn|MovedIn20Warning|PydanticDeprecated" .tmp/test-logs/20260626-141256/Python_static_tests.log
```

Results:

- Passed: Python static tests passed 161 tests with no deprecation warning summary.
- Passed: legacy pytest E2E passed 38 tests.
- Passed: quick gate passed Svelte check, frontend lint, and Python static tests.
- Passed: warning scan found no warning/deprecation matches in the fresh Python static log.

## Known Issues

- Browser/toolchain messages such as macOS WebKit support notices and Node `NO_COLOR`/`FORCE_COLOR` warnings are still emitted by the frontend Playwright toolchain. P2-12 targeted the SQLAlchemy/Pydantic test-warning noise described in the ticket.

## Next Best Step

- Proceed to P2-13 Deployment Topology Documentation.
