from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from backend.core.settings import BackendSettings
from backend.main import create_app


def test_application_factory_owns_framework_wiring():
    application = create_app(
        BackendSettings(
            app_env="test",
            secret_key="test-secret",
            cors_allow_origins=("https://frontend.test",),
            session_https_only=False,
        )
    )

    middleware_types = {middleware.cls for middleware in application.user_middleware}

    assert SessionMiddleware in middleware_types
    assert CORSMiddleware in middleware_types
    assert application.openapi_url is None
    assert application.redoc_url is None
    assert application.state.limiter is not None

    session_middleware = next(
        middleware
        for middleware in application.user_middleware
        if middleware.cls is SessionMiddleware
    )
    assert session_middleware.kwargs["max_age"] == 14 * 24 * 60 * 60
    assert session_middleware.kwargs["same_site"] == "lax"
    assert session_middleware.kwargs["https_only"] is False


def test_explicit_settings_keep_business_routes_registered():
    application = create_app(
        BackendSettings(
            app_env="test",
            secret_key="test-secret",
            cors_allow_origins=(),
            session_https_only=False,
        )
    )

    route_paths = {route.path for route in application.routes}

    assert "/profile/login/" in route_paths
    assert "/internal/run-daily-job" in route_paths


def test_health_and_readiness_endpoints_are_safe_and_database_aware(app_module):
    client = TestClient(app_module.app)
    health = client.get("/healthz")
    readiness = client.get("/readyz")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ready"}


def test_readiness_failure_is_logged_and_non_sensitive(app_module, caplog):
    def fail_readiness():
        raise RuntimeError("database-password-should-not-leak")

    original_check = app_module.app.state.readiness_check
    app_module.app.state.readiness_check = fail_readiness
    try:
        with caplog.at_level("ERROR", logger="backend.main"):
            response = TestClient(app_module.app).get("/readyz")
    finally:
        app_module.app.state.readiness_check = original_check

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert "database-password-should-not-leak" not in response.text
    assert "Database readiness check failed" in caplog.text


def test_request_context_middleware_propagates_and_reuses_request_id():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    application = create_app(
        BackendSettings(
            app_env="test",
            secret_key="test-secret",
            cors_allow_origins=(),
            session_https_only=False,
        )
    )

    @application.get("/test/request-id")
    def request_id():
        return {"ok": True}

    response = TestClient(application).get(
        "/test/request-id",
        headers={"X-Request-ID": "test-request-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-123"


def test_application_factory_invokes_explicit_route_registration():
    registrations = []

    def register_routes(application, *, limiter):
        registrations.append((application, limiter))

    application = create_app(
        BackendSettings(
            app_env="test",
            secret_key="test-secret",
            cors_allow_origins=(),
            session_https_only=False,
        ),
        register_routes=register_routes,
    )

    assert registrations == [(application, application.state.limiter)]
