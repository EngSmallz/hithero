"""Shared test setup.

app.py reads its settings from environment variables and connects to the
database when it is imported. tests/testenv.py supplies test settings.

By default no database is used, so only tests that never query run
(for example the route golden test). With TEST_DATABASE=1 the app talks
to the local SQL Server started by scripts/test_db.sh, and the
database-backed tests run too.
"""
from tests import testenv

testenv.configure()


def update_golden() -> bool:
    """True when the run should rewrite golden files instead of comparing."""
    return testenv.update_golden()


def pytest_sessionfinish(session, exitstatus):
    """Leave the database freshly seeded if any test wrote to it."""
    from tests import helpers

    if helpers.db_dirty:
        helpers.reseed()
