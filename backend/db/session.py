from dataclasses import dataclass
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.settings import LOCAL_APP_ENVS


def build_sql_server_url():
    database_server = os.getenv("DATABASE_SERVER")
    database_name = os.getenv("DATABASE_NAME")
    database_uid = os.getenv("DATABASE_UID")
    database_password = os.getenv("DATABASE_PASSWORD")
    database_port = os.getenv("DATABASE_PORT")
    return (
        f"mssql+pyodbc://{database_uid}:{database_password}@{database_server}:"
        f"{database_port}/{database_name}?driver=ODBC+Driver+18+for+SQL+Server"
    )


def build_database_url(app_env: str):
    explicit_database_url = os.getenv("DATABASE_URL")
    if explicit_database_url:
        return explicit_database_url

    if app_env == "test":
        return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    if app_env in LOCAL_APP_ENVS:
        return os.getenv("LOCAL_DATABASE_URL", "sqlite:///./.local/hithero-dev.sqlite")

    return build_sql_server_url()


def ensure_sqlite_database_directory(database_url: str):
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        return

    database_directory = os.path.dirname(os.path.abspath(url.database))
    if database_directory:
        os.makedirs(database_directory, exist_ok=True)


def build_engine_kwargs(database_url: str):
    url = make_url(database_url)
    engine_options = {}

    if url.drivername.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if url.database == ":memory:":
            engine_options["poolclass"] = StaticPool

    return engine_options


@dataclass(frozen=True)
class DatabaseResources:
    database_url: str
    engine: object
    session_factory: object


def create_database_resources(app_env: str, database_url: str | None = None):
    resolved_url = database_url or build_database_url(app_env)
    ensure_sqlite_database_directory(resolved_url)
    engine = create_engine(resolved_url, **build_engine_kwargs(resolved_url))
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return DatabaseResources(
        database_url=resolved_url,
        engine=engine,
        session_factory=session_factory,
    )


__all__ = [
    "DatabaseResources",
    "build_database_url",
    "build_engine_kwargs",
    "build_sql_server_url",
    "create_database_resources",
    "ensure_sqlite_database_directory",
]
