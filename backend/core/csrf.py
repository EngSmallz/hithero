from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
PROTECTED_PREFIXES = (
    "/profile/",
    "/forum/",
    "/validation/",
    "/admin/",
    "/api/contact_us/",
)
LOCAL_ENVIRONMENTS = frozenset({"", "test", "dev", "development", "local"})


def request_origin(request):
    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/")
    referer = request.headers.get("referer")
    if referer:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return None


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject cross-site unsafe browser mutations in deployed environments."""

    def __init__(self, app, *, app_env, allowed_origins):
        super().__init__(app)
        self._app_env = app_env
        self._allowed_origins = {
            origin.rstrip("/") for origin in allowed_origins
        }

    async def dispatch(self, request, call_next):
        protected = any(
            request.url.path.startswith(prefix) for prefix in PROTECTED_PREFIXES
        )
        if (
            self._app_env not in LOCAL_ENVIRONMENTS
            and request.method in UNSAFE_METHODS
            and protected
            and request_origin(request) not in self._allowed_origins
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed."},
            )
        return await call_next(request)
