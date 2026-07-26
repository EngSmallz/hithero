import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.integrations.providers import (
    AzureEmailProvider,
    RecaptchaProvider,
    XProvider,
)
from backend.routers.compatibility import create_compatibility_router


def test_contact_api_reports_email_provider_failure_without_success_payload(
):
    application = FastAPI()
    application.include_router(
        create_compatibility_router(
            fetch_random_teacher=lambda: None,
            set_teacher_session=lambda _request, _teacher: None,
            verify_recaptcha=lambda _token: True,
            render_email_template=lambda _template, _data: "<p>message</p>",
            send_email=lambda *args: False,
            clean_html=lambda value, **_kwargs: value,
            logger=logging.getLogger("test-provider-failure"),
        )
    )

    response = TestClient(application).post(
        "/api/contact_us/",
        data={
            "name": "Test Sender",
            "email": "sender@example.test",
            "subject": "Test",
            "message": "A test message",
            "recaptcha_response": "hithero-test-recaptcha",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Contact email provider is temporarily unavailable."
    }


class FakePoller:
    def __init__(self, result=None, error=None):
        self.result_value = result
        self.error = error
        self.timeout = None

    def result(self, timeout=None):
        self.timeout = timeout
        if self.error:
            raise self.error
        return self.result_value


class FakeEmailClient:
    poller = None
    last_message = None

    @classmethod
    def from_connection_string(cls, connection_string):
        cls.connection_string = connection_string
        return cls()

    def begin_send(self, message):
        type(self).last_message = message
        return self.poller


def test_azure_email_success_uses_timeout(monkeypatch):
    poller = FakePoller(result="sent")
    FakeEmailClient.poller = poller
    monkeypatch.setenv("AZURE_EMAIL_CONNECTION_STRING", "connection")
    monkeypatch.setenv("AZURE_EMAIL_SENDER", "sender@example.test")

    provider = AzureEmailProvider(
        app_env="production",
        timeout_seconds=3.5,
        client_factory=FakeEmailClient,
    )

    assert provider.send("recipient@example.test", "Subject", "<p>Hi</p>", "Hi")
    assert poller.timeout == 3.5


def test_azure_email_missing_configuration_is_unsuccessful(monkeypatch):
    monkeypatch.delenv("AZURE_EMAIL_CONNECTION_STRING", raising=False)

    provider = AzureEmailProvider(
        app_env="production",
        client_factory=FakeEmailClient,
    )

    assert provider.send("recipient@example.test", "Subject", "<p>Hi</p>", "Hi") is False


def test_azure_email_local_mode_skips_external_provider(monkeypatch):
    monkeypatch.delenv("AZURE_EMAIL_CONNECTION_STRING", raising=False)

    provider = AzureEmailProvider(
        app_env="development",
        client_factory=FakeEmailClient,
    )

    assert provider.send("recipient@example.test", "Subject", "<p>Hi</p>", "Hi") is True


def test_azure_email_timeout_failure_is_unsuccessful(monkeypatch):
    FakeEmailClient.poller = FakePoller(error=TimeoutError("timed out"))
    monkeypatch.setenv("AZURE_EMAIL_CONNECTION_STRING", "connection")

    provider = AzureEmailProvider(
        app_env="production",
        timeout_seconds=1,
        client_factory=FakeEmailClient,
    )

    assert provider.send("recipient@example.test", "Subject", "<p>Hi</p>", "Hi") is False


def test_azure_attachment_success_uses_timeout_and_payload(monkeypatch, tmp_path):
    poller = FakePoller(result="attachment-sent")
    FakeEmailClient.poller = poller
    monkeypatch.setenv("AZURE_EMAIL_CONNECTION_STRING", "connection")
    attachment = tmp_path / "report.txt"
    attachment.write_text("report", encoding="utf-8")

    provider = AzureEmailProvider(
        app_env="production",
        timeout_seconds=4,
        client_factory=FakeEmailClient,
    )

    assert (
        provider.send_attachment(
            "recipient@example.test", "Subject", "See attached", str(attachment)
        )
        == "attachment-sent"
    )
    assert poller.timeout == 4
    assert FakeEmailClient.last_message["attachments"][0]["name"] == "report.txt"


class FakeRecaptchaResponse:
    def __init__(self, successful=True, error=None):
        self.successful = successful
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return {"success": self.successful}


class FakeRecaptchaSession:
    def __init__(self, response):
        self.response = response
        self.timeout = None

    def post(self, _url, *, params, timeout):
        self.params = params
        self.timeout = timeout
        return self.response


def test_recaptcha_test_token_contract():
    provider = RecaptchaProvider(
        app_env="test",
        secret_key=None,
        expected_test_token="expected",
    )

    assert provider.verify("expected") is True
    assert provider.verify("wrong") is False


def test_recaptcha_local_token_contract():
    provider = RecaptchaProvider(
        app_env="development",
        secret_key=None,
        expected_test_token="expected",
    )

    assert provider.verify("expected") is True
    assert provider.verify("wrong") is False


def test_recaptcha_success_uses_timeout():
    session = FakeRecaptchaSession(FakeRecaptchaResponse())
    provider = RecaptchaProvider(
        app_env="production",
        secret_key="secret",
        expected_test_token="unused",
        timeout_seconds=2.5,
        session=session,
    )

    assert provider.verify("response") is True
    assert session.timeout == 2.5
    assert session.params == {"secret": "secret", "response": "response"}


def test_recaptcha_missing_configuration_and_failure_are_false():
    missing_secret = RecaptchaProvider(
        app_env="production",
        secret_key=None,
        expected_test_token="unused",
    )
    failed_session = FakeRecaptchaSession(
        FakeRecaptchaResponse(error=RuntimeError("provider failed"))
    )
    failed_provider = RecaptchaProvider(
        app_env="production",
        secret_key="secret",
        expected_test_token="unused",
        session=failed_session,
    )

    assert missing_secret.verify("response") is False
    assert failed_provider.verify("response") is False


def test_x_provider_success_uses_credentials(monkeypatch):
    credentials = {
        "X_API_KEY": "key",
        "X_API_SECRET": "secret",
        "X_ACCESS_TOKEN": "token",
        "X_ACCESS_TOKEN_SECRET": "token-secret",
    }
    for name, value in credentials.items():
        monkeypatch.setenv(name, value)

    class FakeXClient:
        last_kwargs = None

        def __init__(self, **kwargs):
            type(self).last_kwargs = kwargs

        def create_tweet(self, *, text):
            return {"text": text}

    provider = XProvider(client_factory=FakeXClient)

    assert provider.publish("hello") == {"text": "hello"}
    assert FakeXClient.last_kwargs == {
        "consumer_key": "key",
        "consumer_secret": "secret",
        "access_token": "token",
        "access_token_secret": "token-secret",
    }


def test_x_provider_missing_configuration_and_failure_are_none(monkeypatch):
    for name in (
        "X_API_KEY",
        "X_API_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)

    class UnexpectedClient:
        def __init__(self, **_kwargs):
            raise AssertionError("client should not be constructed")

    assert XProvider(client_factory=UnexpectedClient).publish("hello") is None

    for name, value in {
        "X_API_KEY": "key",
        "X_API_SECRET": "secret",
        "X_ACCESS_TOKEN": "token",
        "X_ACCESS_TOKEN_SECRET": "token-secret",
    }.items():
        monkeypatch.setenv(name, value)

    class FailingClient:
        def __init__(self, **_kwargs):
            pass

        def create_tweet(self, *, text):
            raise RuntimeError("provider failed")

    assert XProvider(client_factory=FailingClient).publish("hello") is None


def test_registration_route_cannot_report_provider_failure_as_success(
    app_module, monkeypatch
):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.NewUsers))
        db.execute(delete(app_module.RegisteredUsers))
        db.commit()
    finally:
        db.close()

    monkeypatch.setattr(app_module.legacy_jobs.email_provider, "send", lambda *args: False)
    app_module.app.state.limiter._storage.reset()
    response = TestClient(app_module.app).post(
        "/profile/register/",
        data={
            "name": "Provider Failure",
            "email": "provider-registration@example.test",
            "phone_number": "555-0180",
            "password": "test-password",
            "confirm_password": "test-password",
            "state": "WA",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Lincoln High School",
            "recaptcha_response": "hithero-test-recaptcha",
        },
    )

    assert response.status_code == 502
    assert "success" not in response.text.lower()


def test_password_reset_route_cannot_report_provider_failure_as_success(
    app_module, monkeypatch
):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.RegisteredUsers))
        db.add(
            app_module.RegisteredUsers(
                email="provider-reset@example.test",
                phone_number="555-0181",
                password=app_module.sha256_crypt.hash("test-password"),
                role="teacher",
                createCount=0,
            )
        )
        db.commit()
    finally:
        db.close()

    monkeypatch.setattr(app_module.legacy_jobs.email_provider, "send", lambda *args: False)
    app_module.app.state.limiter._storage.reset()
    response = TestClient(app_module.app).post(
        "/profile/forgot_password/",
        data={"email": "provider-reset@example.test"},
    )

    assert response.status_code == 502
    assert "reset link will be sent" not in response.text


def seed_provider_admin_data(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.TeacherList))
        db.execute(delete(app_module.NewUsers))
        db.execute(delete(app_module.RegisteredUsers))
        admin = app_module.RegisteredUsers(
            email="provider-admin@example.test",
            phone_number="555-0182",
            password=app_module.sha256_crypt.hash("admin-password"),
            role="admin",
            createCount=0,
        )
        teacher_user = app_module.RegisteredUsers(
            email="provider-teacher@example.test",
            phone_number="555-0183",
            password=app_module.sha256_crypt.hash("teacher-password"),
            role="teacher",
            createCount=1,
        )
        db.add_all([admin, teacher_user])
        db.flush()
        db.add(
            app_module.TeacherList(
                name="Provider Teacher",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Lincoln High School",
                regUserID=teacher_user.id,
                url_id="provider-teacher",
            )
        )
        db.add(
            app_module.NewUsers(
                name="Pending Provider Teacher",
                email="provider-pending@example.test",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Roosevelt High School",
                phone_number="555-0184",
                password=app_module.sha256_crypt.hash("pending-password"),
                role="teacher",
                report=0,
                emailed=0,
            )
        )
        db.commit()
    finally:
        db.close()


def login_provider_admin(app_module):
    app_module.app.state.limiter._storage.reset()
    client = TestClient(app_module.app)
    assert client.post(
        "/profile/login/",
        data={"email": "provider-admin@example.test", "password": "admin-password"},
    ).status_code == 200
    return client


def test_validation_route_cannot_report_provider_failure_as_success(
    app_module, monkeypatch
):
    seed_provider_admin_data(app_module)
    monkeypatch.setattr(app_module.legacy_jobs.email_provider, "send", lambda *args: False)

    response = login_provider_admin(app_module).post(
        "/validation/validate_user/provider-pending@example.test"
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Validation email provider is temporarily unavailable."
    )


def test_teacher_report_route_cannot_report_provider_failure_as_success(
    app_module, monkeypatch
):
    seed_provider_admin_data(app_module)
    monkeypatch.setattr(
        app_module.legacy_jobs.email_provider,
        "send_attachment",
        lambda *args, **kwargs: False,
    )

    response = login_provider_admin(app_module).post(
        "/admin/generate_teacher_report/",
        data={"state": "WA"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Report email provider is temporarily unavailable."
    )
