from pathlib import Path


def test_database_url_prefers_explicit_database_url(app_module, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom.sqlite")
    monkeypatch.setenv("TEST_DATABASE_URL", "sqlite:///./ignored-test.sqlite")

    assert app_module.build_database_url("test") == "sqlite:///./custom.sqlite"
    assert app_module.build_database_url("production") == "sqlite:///./custom.sqlite"


def test_test_env_uses_test_database_url(app_module, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("TEST_DATABASE_URL", "sqlite:///./.tmp/hithero-test.sqlite")

    assert app_module.build_database_url("test") == "sqlite:///./.tmp/hithero-test.sqlite"


def test_test_env_defaults_to_memory_sqlite(app_module, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    assert app_module.build_database_url("test") == "sqlite:///:memory:"


def test_development_env_defaults_to_local_sqlite(app_module, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_DATABASE_URL", raising=False)

    assert app_module.build_database_url("development") == "sqlite:///./.local/hithero-dev.sqlite"


def test_development_env_can_use_local_database_url(app_module, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("LOCAL_DATABASE_URL", "sqlite:///./.local/alternate.sqlite")

    assert app_module.build_database_url("local") == "sqlite:///./.local/alternate.sqlite"


def test_sqlite_database_directory_is_created(app_module, tmp_path):
    database_path = tmp_path / "nested" / "test.sqlite"

    app_module.ensure_sqlite_database_directory(f"sqlite:///{database_path}")

    assert database_path.parent.is_dir()
    assert not database_path.exists()


def test_database_random_ordering_uses_sqlite_random_in_test_mode(app_module):
    assert app_module.SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    assert "random" in str(app_module.database_random_ordering()).lower()
    assert "newid" not in str(app_module.database_random_ordering()).lower()


def test_in_memory_sqlite_engine_uses_static_pool(app_module):
    engine_kwargs = app_module.build_engine_kwargs("sqlite:///:memory:")

    assert engine_kwargs["connect_args"] == {"check_same_thread": False}
    assert engine_kwargs["poolclass"] is app_module.StaticPool


def test_file_sqlite_engine_does_not_use_static_pool(app_module, tmp_path):
    engine_kwargs = app_module.build_engine_kwargs(f"sqlite:///{tmp_path / 'test.sqlite'}")

    assert engine_kwargs["connect_args"] == {"check_same_thread": False}
    assert "poolclass" not in engine_kwargs


def test_init_db_creates_file_backed_sqlite_database(app_module, tmp_path, monkeypatch):
    database_path = tmp_path / "hithero-test.sqlite"
    database_url = f"sqlite:///{database_path}"

    monkeypatch.setenv("DATABASE_URL", database_url)
    assert app_module.build_database_url("test") == database_url
    app_module.ensure_sqlite_database_directory(database_url)

    engine = app_module.create_engine(database_url, connect_args={"check_same_thread": False})
    app_module.Base.metadata.create_all(bind=engine)
    engine.dispose()

    assert Path(database_path).is_file()


def test_local_cors_origins_include_sveltekit_dev_server(app_module, monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)

    origins = app_module.get_cors_allow_origins("development")

    assert "https://www.helpteachers.net" in origins
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins


def test_cors_origins_can_be_configured(app_module, monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://frontend.test, https://example.test ")

    assert app_module.get_cors_allow_origins("development") == [
        "http://frontend.test",
        "https://example.test",
    ]


def test_session_cookies_are_secure_outside_local_and_test(app_module):
    assert app_module.session_cookie_https_only("production") is True
    assert app_module.session_cookie_https_only("") is True
    assert app_module.session_cookie_https_only("development") is False
    assert app_module.session_cookie_https_only("local") is False
    assert app_module.session_cookie_https_only("test") is False
