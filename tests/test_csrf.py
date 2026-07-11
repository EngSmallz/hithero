from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.core.settings import BackendSettings
from backend.core.errors import BadRequestError
from backend.main import create_app


def make_production_app():
    application = create_app(
        BackendSettings(
            app_env="production",
            secret_key="test-secret",
            cors_allow_origins=("https://www.helpteachers.net",),
            session_https_only=True,
        )
    )

    @application.post("/profile/test-mutation")
    def mutate():
        return {"ok": True}

    @application.get("/profile/test-read")
    def read():
        return {"ok": True}

    return application


def test_csrf_middleware_rejects_unsafe_cross_site_mutations():
    response = TestClient(make_production_app()).post("/profile/test-mutation")

    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF validation failed."}


def test_csrf_middleware_accepts_configured_origin_and_same_origin_referer():
    client = TestClient(make_production_app())

    origin_response = client.post(
        "/profile/test-mutation",
        headers={"Origin": "https://www.helpteachers.net"},
    )
    referer_response = client.post(
        "/profile/test-mutation",
        headers={"Referer": "https://www.helpteachers.net/profile/edit"},
    )

    assert origin_response.status_code == 200
    assert referer_response.status_code == 200


def test_csrf_middleware_does_not_block_safe_reads():
    response = TestClient(make_production_app()).get(
        "/profile/test-read",
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 200


def test_domain_errors_use_one_stable_http_mapping():
    application = create_app(
        BackendSettings(
            app_env="test",
            secret_key="test-secret",
            cors_allow_origins=(),
            session_https_only=False,
        )
    )

    @application.get("/typed-error")
    def typed_error():
        raise BadRequestError("Invalid typed request")

    response = TestClient(application).get("/typed-error")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid typed request"}
