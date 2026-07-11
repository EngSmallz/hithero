from fastapi.middleware.cors import CORSMiddleware
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
