from dataclasses import dataclass
import os


LOCAL_APP_ENVS = frozenset({"dev", "development", "local"})
PRODUCTION_CORS_ORIGINS = ("https://www.helpteachers.net", "https://helpteachers.net")
LOCAL_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
)
SESSION_MAX_AGE_SECONDS = 14 * 24 * 60 * 60
SESSION_SAME_SITE = "lax"


def get_cors_allow_origins(app_env: str, environ=None):
    environment = os.environ if environ is None else environ
    configured_origins = environment.get("CORS_ALLOW_ORIGINS")
    if configured_origins:
        return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

    origins = list(PRODUCTION_CORS_ORIGINS)
    if app_env == "test" or app_env in LOCAL_APP_ENVS:
        origins.extend(LOCAL_CORS_ORIGINS)

    return origins


def session_cookie_https_only(app_env: str):
    return app_env != "test" and app_env not in LOCAL_APP_ENVS


@dataclass(frozen=True)
class BackendSettings:
    """Settings needed to construct the FastAPI application shell.

    Database and provider settings remain in their current compatibility
    locations until their B1/B2 extraction slices. Keeping this object small
    makes the application factory testable without changing those contracts.
    """

    app_env: str
    secret_key: str | None
    cors_allow_origins: tuple[str, ...]
    session_https_only: bool
    session_max_age_seconds: int = SESSION_MAX_AGE_SECONDS
    session_same_site: str = SESSION_SAME_SITE
    static_dir: str = "static"
    provider_timeout_seconds: float = 10.0

    @classmethod
    def from_environment(cls):
        app_env = os.getenv("APP_ENV", "").lower()
        return cls(
            app_env=app_env,
            secret_key=os.getenv("SECRET_KEY"),
            cors_allow_origins=tuple(get_cors_allow_origins(app_env)),
            session_https_only=session_cookie_https_only(app_env),
            provider_timeout_seconds=float(
                os.getenv("PROVIDER_TIMEOUT_SECONDS", "10")
            ),
        )
