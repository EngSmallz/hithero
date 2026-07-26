from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.repositories.profile import ProfileRepository
from backend.services.profile_auth import ProfileAuthService


class RecordingRepository:
    def __init__(self, *, registered=None, pending=None):
        self.registered = registered
        self.pending = pending
        self.created = None

    def get_registered_user_by_email(self, _email):
        return self.registered

    def get_pending_user_by_email(self, _email):
        return self.pending

    def create_pending_user(self, **values):
        self.created = values


def registration_values(**overrides):
    values = {
        "name": "New Teacher",
        "email": "new-teacher@example.test",
        "phone_number": "555-0101",
        "password": "new-password",
        "confirm_password": "new-password",
        "state": "WA",
        "county": "King",
        "district": "Seattle Public Schools",
        "school": "Lincoln High School",
    }
    values.update(overrides)
    return values


def test_profile_auth_service_registers_and_hashes_pending_user():
    repository = RecordingRepository()
    service = ProfileAuthService(repository)

    message, send_email = service.register_user(**registration_values())

    assert message.startswith("User registered successfully.")
    assert send_email is True
    assert repository.created["email"] == "new-teacher@example.test"
    assert repository.created["password"] != "new-password"
    assert service.authenticate_user(
        "new-teacher@example.test", "new-password"
    ) is None


@pytest.mark.parametrize(
    ("repository", "overrides", "expected"),
    [
        (
            RecordingRepository(registered=object()),
            {},
            "User with this email already exists.",
        ),
        (
            RecordingRepository(pending=object()),
            {},
            "User with this email is already in the registration queue.",
        ),
        (
            RecordingRepository(),
            {"confirm_password": "different"},
            "Password do not match.",
        ),
    ],
)
def test_profile_auth_service_preserves_registration_guards(
    repository, overrides, expected
):
    message, send_email = ProfileAuthService(repository).register_user(
        **registration_values(**overrides)
    )

    assert message == expected
    assert send_email is False
    assert repository.created is None


def test_profile_auth_service_authenticates_valid_and_invalid_passwords():
    from passlib.hash import sha256_crypt

    user = SimpleNamespace(
        email="teacher@example.test",
        password=sha256_crypt.hash("correct-password"),
        role="teacher",
        id=42,
        createCount=1,
    )
    service = ProfileAuthService(RecordingRepository(registered=user))

    assert service.authenticate_user("teacher@example.test", "correct-password") is user
    assert service.authenticate_user("teacher@example.test", "wrong-password") is None


class FailingAddSession:
    def __init__(self):
        self.rollback_called = False
        self.closed = False

    def add(self, _model):
        raise RuntimeError("insert failed")

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.closed = True


def test_profile_repository_rolls_back_and_closes_failed_registration_insert(
    app_module,
):
    session = FailingAddSession()
    repository = ProfileRepository(
        session_factory=lambda: session,
        teacher_model=app_module.TeacherList,
        pending_user_model=app_module.NewUsers,
    )

    with pytest.raises(RuntimeError, match="insert failed"):
        values = registration_values()
        values.pop("confirm_password")
        repository.create_pending_user(**values)

    assert session.rollback_called is True
    assert session.closed is True


def test_registration_api_preserves_recaptcha_and_pending_user_contract(
    app_module,
):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.NewUsers))
        db.execute(delete(app_module.RegisteredUsers))
        db.commit()
    finally:
        db.close()


def test_logout_preserves_browser_redirect_and_returns_json_to_api_clients(app_module):
    client = TestClient(app_module.app)

    api_response = client.post(
        "/profile/logout/",
        headers={"accept": "application/json"},
    )
    browser_response = client.post(
        "/profile/logout/",
        headers={"accept": "text/html"},
        follow_redirects=False,
    )

    assert api_response.status_code == 200
    assert api_response.json() == {"message": "Logged out successfully."}
    assert browser_response.status_code == 303
    assert browser_response.headers["location"] == "/"

    response = TestClient(app_module.app).post(
        "/profile/register/",
        data={
            **registration_values(email="api-register@example.test"),
            "recaptcha_response": app_module.TEST_RECAPTCHA_TOKEN,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": (
            "User registered successfully. You should recieve an email shortly. "
            "Please check your spam folder"
        )
    }
    db = app_module.SessionLocal()
    try:
        user = db.query(app_module.NewUsers).filter_by(
            email="api-register@example.test"
        ).one()
        assert app_module.sha256_crypt.verify("new-password", user.password)
        assert user.role == "teacher"
        assert user.report == 0
        assert user.emailed == 0
    finally:
        db.close()
