from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.core.csrf import CSRFMiddleware
from backend.core.errors import DomainError, domain_error_handler
from backend.core.settings import BackendSettings

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


def create_app(settings: BackendSettings | None = None):
    """Create the FastAPI application shell used by the modular monolith.

    Domain routers are still registered by the compatibility ``app.py`` entry
    point in this first B1 slice. This factory owns only framework wiring so
    later slices can move registrations without changing middleware behavior.
    """

    settings = settings or BackendSettings.from_environment()
    application = FastAPI(openapi_url=None, redoc_url=None)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
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

    limiter = Limiter(key_func=get_remote_address)
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_exception_handler(DomainError, domain_error_handler)
    application.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    return application


__all__ = ["BackendSettings", "create_app"]
