"""Environment for importing app.py outside production.

Shared by the tests and by tests/seed.py. Must run before app.py is
imported, because app.py reads settings and builds its engine on import.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEST_ENV = {
    "SECRET_KEY": "test-secret-key",
    "DATABASE_SERVER": "localhost",
    "DATABASE_NAME": "hithero_test",
    "DATABASE_UID": "sa",
    "DATABASE_PASSWORD": "Test_Passw0rd!",
    "DATABASE_PORT": "1433",
    "INTERNAL_JOB_SECRET": "test-job-secret",
    "admin_secret": "test-admin-secret",
    "BASE_URL": "https://testserver",
    "AZURE_EMAIL_CONNECTION_STRING": "endpoint=https://fake.invalid/;accesskey=ZmFrZQ==",
    "AZURE_EMAIL_SENDER": "DoNotReply@test.invalid",
}

_configured = False


def use_database() -> bool:
    return os.environ.get("TEST_DATABASE") == "1"


def update_golden() -> bool:
    return os.environ.get("UPDATE_GOLDEN") == "1"


def configure(force_database: bool = False) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)  # app.py mounts "pages" and "static" by relative path
    for key, value in TEST_ENV.items():
        os.environ.setdefault(key, value)

    import sqlalchemy

    if force_database or use_database():
        # The local container uses a self-signed certificate, which ODBC
        # Driver 18 rejects by default. app.py builds its URL with an
        # f-string, so add TrustServerCertificate here. BE2-4 replaces this
        # with a setting in db.py.
        real_create_engine = sqlalchemy.create_engine

        def create_engine(url, *args, **kwargs):
            url = sqlalchemy.engine.make_url(url).update_query_dict(
                {"TrustServerCertificate": "yes"}
            )
            # Tests drop and recreate the database between write tests, and
            # some handlers leave their session open, so a pooled connection
            # can be dead by the next test. BE2-4 adds pool_pre_ping in
            # database.py; until then, set it here.
            kwargs.setdefault("pool_pre_ping", True)
            return real_create_engine(url, *args, **kwargs)

        sqlalchemy.create_engine = create_engine

    # Stop app.py's import-time create_all. Without a database it would try
    # to connect; with one, the tables come from tests/seed.py instead
    # (see the note there on why create_all cannot build them as-is).
    import sqlalchemy.sql.schema

    global real_create_all
    real_create_all = sqlalchemy.sql.schema.MetaData.create_all
    sqlalchemy.sql.schema.MetaData.create_all = lambda *args, **kwargs: None


real_create_all = None
