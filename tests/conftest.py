import importlib
import os
from pathlib import Path

import pytest


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret")

ROOT_DIR = Path(__file__).resolve().parents[1]


def isolate_xdist_sqlite_database():
    worker = os.getenv("PYTEST_XDIST_WORKER")
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if not worker or not test_database_url or os.getenv("DATABASE_URL"):
        return

    if test_database_url == "sqlite:///:memory:" or not test_database_url.startswith("sqlite:///"):
        return

    database_name = test_database_url.removeprefix("sqlite:///")
    if not database_name or database_name == ":memory:":
        return

    database_path = Path(database_name)
    if not database_path.is_absolute():
        database_path = ROOT_DIR / database_path

    worker_path = database_path.with_name(f"{database_path.stem}-{worker}{database_path.suffix}")
    worker_path.parent.mkdir(parents=True, exist_ok=True)

    os.environ["TEST_DATABASE_URL"] = f"sqlite:///{worker_path}"


isolate_xdist_sqlite_database()


@pytest.fixture(scope="session")
def app_module():
    return importlib.import_module("app")
