from backend.db.session import create_database_resources


def test_database_resources_create_a_shared_in_memory_sqlite_session_factory():
    resources = create_database_resources("test", "sqlite:///:memory:")

    try:
        assert resources.database_url == "sqlite:///:memory:"
        assert resources.engine.pool.__class__.__name__ == "StaticPool"
        assert resources.session_factory.kw["bind"] is resources.engine
    finally:
        resources.engine.dispose()
