import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.core.csrf import CSRFMiddleware
from backend.core.errors import DomainError, domain_error_handler
from backend.core.observability import RequestContextMiddleware
from backend.core.settings import BackendSettings, LOCAL_APP_ENVS
from backend.api.composition import register_application_routes
from backend.db.base import Base
from backend.db.session import DatabaseResources, create_database_resources
from backend.integrations.providers import (
    AzureEmailProvider,
    RecaptchaProvider,
    XProvider,
    render_email_template,
)
from backend.jobs.legacy import LegacyJobService


logger = logging.getLogger(__name__)

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
except ImportError:
    class RateLimitExceeded(Exception):
        pass

    def _rate_limit_exceeded_handler(request, exc):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    def get_remote_address(request):
        client = getattr(request, "client", None)
        return client.host if client else "testclient"

    class Limiter:
        def __init__(self, key_func):
            self.key_func = key_func

        def limit(self, _limit):
            def decorator(func):
                return func

            return decorator


def _unconfigured_database_resources():
    def unavailable_session_factory():
        raise RuntimeError("Database resources are not configured")

    return DatabaseResources(
        database_url="unconfigured",
        engine=None,
        session_factory=unavailable_session_factory,
    )


def _has_production_database_configuration():
    if os.getenv("DATABASE_URL"):
        return True
    return all(
        os.getenv(name)
        for name in (
            "DATABASE_SERVER",
            "DATABASE_NAME",
            "DATABASE_UID",
            "DATABASE_PASSWORD",
            "DATABASE_PORT",
        )
    )


def create_app(settings: BackendSettings | None = None, *, register_routes=None):
    """Create the FastAPI application shell used by the modular monolith.

    The module-level ``app`` uses this factory as the composition root. Tests
    may pass explicit settings or an explicit route registrar without losing
    the application route graph.
    """

    settings_was_injected = settings is not None
    settings = settings or BackendSettings.from_environment()
    database_resources = None
    application = FastAPI(openapi_url=None, redoc_url=None)
    application.state.database_resources = None
    application.state.legacy_jobs = None

    if (
        settings_was_injected
        and settings.app_env not in LOCAL_APP_ENVS | {"test"}
        and not _has_production_database_configuration()
    ):
        database_resources = _unconfigured_database_resources()
    else:
        database_resources = create_database_resources(settings.app_env)
    application.state.database_resources = database_resources

    if settings.app_env in LOCAL_APP_ENVS:
        Base.metadata.create_all(bind=database_resources.engine)

    email_provider = AzureEmailProvider(
        app_env=settings.app_env,
        timeout_seconds=settings.provider_timeout_seconds,
    )
    recaptcha_provider = RecaptchaProvider(
        app_env=settings.app_env,
        secret_key=os.getenv("SERVER_KEY_CAPTCHA"),
        expected_test_token=os.getenv(
            "TEST_RECAPTCHA_TOKEN", "hithero-test-recaptcha"
        ),
        timeout_seconds=settings.provider_timeout_seconds,
    )
    legacy_jobs = LegacyJobService(
        session_factory=database_resources.session_factory,
        database_url=database_resources.database_url,
        email_provider=email_provider,
        recaptcha_provider=recaptcha_provider,
        x_provider=XProvider(),
        render_email_template=render_email_template,
    )
    application.state.legacy_jobs = legacy_jobs

    def database_ready():
        db = database_resources.session_factory()
        try:
            from sqlalchemy import text

            db.execute(text("SELECT 1"))
        finally:
            db.close()

    application.state.readiness_check = database_ready

    @application.get("/healthz", include_in_schema=False)
    def healthz():
        return {"status": "ok"}

    @application.get("/readyz", include_in_schema=False)
    def readyz():
        try:
            application.state.readiness_check()
        except Exception:
            logger.exception("Database readiness check failed")
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready"},
            )
        return {"status": "ready"}

    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=settings.session_max_age_seconds,
        same_site=settings.session_same_site,
        https_only=settings.session_https_only,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    application.add_middleware(
        CSRFMiddleware,
        app_env=settings.app_env,
        allowed_origins=settings.cors_allow_origins,
    )
    application.add_middleware(RequestContextMiddleware)

    limiter = Limiter(key_func=get_remote_address)
    application.state.limiter = limiter
    if register_routes is not None:
        register_routes(application, limiter=limiter)
    else:
        register_application_routes(
            application,
            database_resources=database_resources,
            legacy_jobs=legacy_jobs,
            limiter=limiter,
            static_dir=settings.static_dir,
        )
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_exception_handler(DomainError, domain_error_handler)
    application.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    return application


app = create_app()
legacy_jobs = app.state.legacy_jobs


__all__ = ["BackendSettings", "app", "create_app", "legacy_jobs"]
