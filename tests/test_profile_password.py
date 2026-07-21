import pytest
from fastapi.testclient import TestClient
from passlib.hash import sha256_crypt
from sqlalchemy import delete

from backend.repositories.profile import ProfileRepository
from backend.services.profile_password import (
    InvalidResetToken,
    PasswordMismatch,
    ProfilePasswordService,
)


class RecordingRepository:
    def __init__(self, password_hash):
        self.password_hash = password_hash
        self.updated = None

    def get_password_hash(self, _user_id):
        return self.password_hash

    def update_password(self, user_id, password_hash):
        self.updated = (user_id, password_hash)


class ResetRepository(RecordingRepository):
    def __init__(self, password_hash, *, reset=None, user_exists=True):
        super().__init__(password_hash)
        self.reset = reset
        self.user_exists = user_exists
        self.created_reset = None
        self.consumed_reset = None

    def get_registered_user_by_email(self, _email):
        return object() if self.user_exists else None

    def create_reset_token(self, **values):
        self.created_reset = values

    def get_valid_reset_token(self, _token, *, now):
        return self.reset

    def consume_reset_token(self, token, email, password_hash):
        self.consumed_reset = (token, email, password_hash)


def test_profile_password_service_preserves_mismatch_and_old_password_guards():
    repository = RecordingRepository(sha256_crypt.hash("old-password"))
    service = ProfilePasswordService(repository)

    assert service.update_password(42, "old-password", "new", "different") == {
        "message": "New passwords do not match."
    }
    assert repository.updated is None

    assert service.update_password(42, "wrong-password", "new", "new") == {
        "message": "Invalid old password"
    }
    assert repository.updated is None


def test_profile_password_service_hashes_and_persists_valid_update():
    repository = RecordingRepository(sha256_crypt.hash("old-password"))
    service = ProfilePasswordService(repository)

    result = service.update_password(42, "old-password", "new-password", "new-password")

    assert result == {
        "status": "success",
        "message": "Password updated successfully",
    }
    assert repository.updated[0] == 42
    assert sha256_crypt.verify("new-password", repository.updated[1])


def test_profile_password_service_creates_reset_token_only_for_existing_users():
    repository = ResetRepository("")
    service = ProfilePasswordService(repository)

    assert service.create_reset_token(
        "teacher@example.test",
        token="reset-token",
        expires_at="tomorrow",
    ) is True
    assert repository.created_reset == {
        "email": "teacher@example.test",
        "token": "reset-token",
        "expires_at": "tomorrow",
    }

    missing = ResetRepository("", user_exists=False)
    assert ProfilePasswordService(missing).create_reset_token(
        "missing@example.test",
        token="missing-token",
        expires_at="tomorrow",
    ) is False
    assert missing.created_reset is None


def test_profile_password_service_validates_and_consumes_reset_token():
    reset = type("Reset", (), {"email": "teacher@example.test"})()
    repository = ResetRepository("", reset=reset)
    service = ProfilePasswordService(repository)

    with pytest.raises(PasswordMismatch):
        service.reset_password(
            "reset-token", "new-password", "different", now="now"
        )

    service.reset_password(
        "reset-token", "new-password", "new-password", now="now"
    )
    assert repository.consumed_reset[0:2] == (
        "reset-token",
        "teacher@example.test",
    )
    assert sha256_crypt.verify("new-password", repository.consumed_reset[2])

    invalid = ProfilePasswordService(ResetRepository("", reset=None))
    with pytest.raises(InvalidResetToken):
        invalid.reset_password(
            "expired-token", "new-password", "new-password", now="now"
        )


class FailingSession:
    def __init__(self):
        self.rollback_called = False
        self.closed = False

    def execute(self, _query):
        raise RuntimeError("password update failed")

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.closed = True


def test_profile_repository_rolls_back_and_closes_failed_password_update(
    app_module,
):
    session = FailingSession()
    repository = ProfileRepository(
        session_factory=lambda: session,
        teacher_model=app_module.TeacherList,
        registered_user_model=app_module.RegisteredUsers,
    )

    with pytest.raises(RuntimeError, match="password update failed"):
        repository.update_password(42, "new-hash")

    assert session.rollback_called is True
    assert session.closed is True


def test_profile_repository_rolls_back_and_closes_failed_reset_consumption(
    app_module,
):
    session = FailingSession()
    repository = ProfileRepository(
        session_factory=lambda: session,
        teacher_model=app_module.TeacherList,
        registered_user_model=app_module.RegisteredUsers,
        reset_token_model=app_module.PasswordResetToken,
    )

    with pytest.raises(RuntimeError, match="password update failed"):
        repository.consume_reset_token("reset-token", "user@example.test", "hash")

    assert session.rollback_called is True
    assert session.closed is True


def test_update_password_api_preserves_authenticated_response_contract(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.TeacherList))
        db.execute(delete(app_module.RegisteredUsers))
        db.add(
            app_module.RegisteredUsers(
                email="password-update@example.test",
                phone_number="555-0192",
                password=sha256_crypt.hash("old-password"),
                role="teacher",
                createCount=0,
            )
        )
        db.commit()
    finally:
        db.close()

    app_module.app.state.limiter._storage.reset()
    client = TestClient(app_module.app)
    login = client.post(
        "/profile/login/",
        data={
            "email": "password-update@example.test",
            "password": "old-password",
        },
    )
    assert login.status_code == 200

    mismatch = client.post(
        "/profile/update_password/",
        data={
            "old_password": "old-password",
            "new_password": "new-password",
            "new_password_confirmed": "different",
        },
    )
    assert mismatch.status_code == 200
    assert mismatch.json() == {"message": "New passwords do not match."}

    updated = client.post(
        "/profile/update_password/",
        data={
            "old_password": "old-password",
            "new_password": "new-password",
            "new_password_confirmed": "new-password",
        },
    )
    assert updated.status_code == 200
    assert updated.json() == {
        "status": "success",
        "message": "Password updated successfully",
    }

    db = app_module.SessionLocal()
    try:
        user = db.query(app_module.RegisteredUsers).filter_by(
            email="password-update@example.test"
        ).one()
        assert sha256_crypt.verify("new-password", user.password)
    finally:
        db.close()


def test_password_reset_api_preserves_token_and_response_contract(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.PasswordResetToken))
        db.execute(delete(app_module.RegisteredUsers))
        db.add(
            app_module.RegisteredUsers(
                email="password-reset@example.test",
                phone_number="555-0193",
                password=sha256_crypt.hash("old-password"),
                role="teacher",
                createCount=0,
            )
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(app_module.app)
    forgot = client.post(
        "/profile/forgot_password/",
        data={"email": "password-reset@example.test"},
    )
    assert forgot.status_code == 200
    assert forgot.json() == {
        "message": "If an account exists, a reset link will be sent to your email."
    }

    db = app_module.SessionLocal()
    try:
        token = db.query(app_module.PasswordResetToken).filter_by(
            email="password-reset@example.test"
        ).one().token
    finally:
        db.close()

    mismatch = client.post(
        "/profile/reset_password/",
        data={
            "token": token,
            "new_password": "new-password",
            "confirm_password": "different",
        },
    )
    assert mismatch.status_code == 400
    assert mismatch.json() == {"detail": "Passwords do not match."}

    reset = client.post(
        "/profile/reset_password/",
        data={
            "token": token,
            "new_password": "new-password",
            "confirm_password": "new-password",
        },
    )
    assert reset.status_code == 200
    assert reset.json() == {
        "message": "Password reset successfully. You can now log in."
    }

    db = app_module.SessionLocal()
    try:
        user = db.query(app_module.RegisteredUsers).filter_by(
            email="password-reset@example.test"
        ).one()
        reset_token = db.query(app_module.PasswordResetToken).filter_by(
            token=token
        ).one()
        assert sha256_crypt.verify("new-password", user.password)
        assert reset_token.used == 1
    finally:
        db.close()
