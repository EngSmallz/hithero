import pytest
from fastapi.testclient import TestClient
from passlib.hash import sha256_crypt
from sqlalchemy import delete

from backend.repositories.profile import ProfileRepository
from backend.services.profile_password import ProfilePasswordService


class RecordingRepository:
    def __init__(self, password_hash):
        self.password_hash = password_hash
        self.updated = None

    def get_password_hash(self, _user_id):
        return self.password_hash

    def update_password(self, user_id, password_hash):
        self.updated = (user_id, password_hash)


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
