import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.repositories.admin import AdminRepository
from backend.services.admin import AdminService, PendingUserNotFound, UserAccountNotFound


class RecordingRepository:
    def __init__(self, deleted=True):
        self.deleted = deleted
        self.target_email = None

    def delete_user_account(self, target_email):
        self.target_email = target_email
        return self.deleted

    def delete_pending_user(self, user_email):
        self.pending_email = user_email
        return self.deleted

    def validate_pending_user(self, user_email, **values):
        self.validated_email = user_email
        self.validation_values = values
        return (user_email if self.deleted else None, None if self.deleted else "missing")


def test_admin_service_deletes_account_and_preserves_message():
    repository = RecordingRepository()
    service = AdminService(repository)

    message = service.delete_user_account("target@example.test")

    assert repository.target_email == "target@example.test"
    assert message == (
        "Successfully deleted account and associated data for target user: "
        "target@example.test."
    )


def test_admin_service_maps_missing_account_to_domain_error():
    service = AdminService(RecordingRepository(deleted=False))

    with pytest.raises(UserAccountNotFound, match="target@example.test"):
        service.delete_user_account("target@example.test")


def test_admin_service_deletes_pending_user_and_maps_missing_user():
    repository = RecordingRepository()
    service = AdminService(repository)
    service.delete_pending_user("pending@example.test")
    assert repository.pending_email == "pending@example.test"

    with pytest.raises(PendingUserNotFound):
        AdminService(RecordingRepository(deleted=False)).delete_pending_user(
            "missing@example.test"
        )


class FailingSession:
    def __init__(self):
        self.rollback_called = False
        self.closed = False

    def execute(self, _query):
        raise RuntimeError("delete failed")

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.closed = True


def test_admin_repository_rolls_back_and_closes_failed_account_deletion(
    app_module,
):
    session = FailingSession()
    repository = AdminRepository(
        session_factory=lambda: session,
        registered_user_model=app_module.RegisteredUsers,
        teacher_model=app_module.TeacherList,
    )

    with pytest.raises(RuntimeError, match="delete failed"):
        repository.delete_user_account("target@example.test")

    assert session.rollback_called is True
    assert session.closed is True


def test_admin_repository_rolls_back_and_closes_failed_pending_deletion(
    app_module,
):
    session = FailingSession()
    repository = AdminRepository(
        session_factory=lambda: session,
        registered_user_model=app_module.RegisteredUsers,
        teacher_model=app_module.TeacherList,
        pending_user_model=app_module.NewUsers,
    )

    with pytest.raises(RuntimeError, match="delete failed"):
        repository.delete_pending_user("pending@example.test")

    assert session.rollback_called is True
    assert session.closed is True


def test_admin_service_validates_pending_user_with_scope_inputs():
    repository = RecordingRepository()
    service = AdminService(repository)

    assert service.validate_pending_user(
        "pending@example.test",
        role="teacher",
        current_user_id=42,
    ) == "pending@example.test"
    assert repository.validated_email == "pending@example.test"
    assert repository.validation_values == {
        "role": "teacher",
        "current_user_id": 42,
    }


def test_admin_repository_rolls_back_and_closes_failed_validation(app_module):
    session = FailingSession()
    repository = AdminRepository(
        session_factory=lambda: session,
        registered_user_model=app_module.RegisteredUsers,
        teacher_model=app_module.TeacherList,
        pending_user_model=app_module.NewUsers,
    )

    with pytest.raises(RuntimeError, match="delete failed"):
        repository.validate_pending_user(
            "pending@example.test",
            role="admin",
            current_user_id=None,
        )

    assert session.rollback_called is True
    assert session.closed is True


def test_admin_delete_account_api_preserves_auth_secret_and_success_contract(
    app_module,
    monkeypatch,
):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.TeacherList))
        db.execute(delete(app_module.RegisteredUsers))
        admin = app_module.RegisteredUsers(
            email="admin-delete@example.test",
            phone_number="555-0190",
            password=app_module.sha256_crypt.hash("admin-password"),
            role="admin",
            createCount=0,
        )
        target = app_module.RegisteredUsers(
            email="target-delete@example.test",
            phone_number="555-0191",
            password=app_module.sha256_crypt.hash("target-password"),
            role="teacher",
            createCount=1,
        )
        db.add_all([admin, target])
        db.flush()
        db.add(
            app_module.TeacherList(
                name="Target Teacher",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Lincoln High School",
                regUserID=target.id,
                url_id="target-delete",
            )
        )
        db.commit()
    finally:
        db.close()

    app_module.app.state.limiter._storage.reset()
    monkeypatch.setenv("admin_secret", "test-admin-secret")
    client = TestClient(app_module.app)
    login = client.post(
        "/profile/login/",
        data={
            "email": "admin-delete@example.test",
            "password": "admin-password",
        },
    )
    assert login.status_code == 200

    response = client.post(
        "/profile/delete/",
        data={
            "target_email": "target-delete@example.test",
            "admin_secret_input": "test-admin-secret",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": (
            "Successfully deleted account and associated data for target user: "
            "target-delete@example.test."
        )
    }

    db = app_module.SessionLocal()
    try:
        assert db.query(app_module.RegisteredUsers).filter_by(
            email="target-delete@example.test"
        ).first() is None
        assert db.query(app_module.TeacherList).filter_by(
            url_id="target-delete"
        ).first() is None
    finally:
        db.close()


def test_validate_user_api_preserves_scope_and_promotion_contract(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.TeacherList))
        db.execute(delete(app_module.RegisteredUsers))
        db.execute(delete(app_module.NewUsers))
        teacher = app_module.RegisteredUsers(
            email="validator@example.test",
            phone_number="555-0194",
            password=app_module.sha256_crypt.hash("validator-password"),
            role="teacher",
            createCount=1,
        )
        db.add(teacher)
        db.flush()
        db.add(
            app_module.TeacherList(
                name="Validator Teacher",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Lincoln High School",
                regUserID=teacher.id,
                url_id="validator-teacher",
            )
        )
        db.add(
            app_module.NewUsers(
                name="Pending Teacher",
                email="pending-validation@example.test",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Roosevelt High School",
                phone_number="555-0195",
                password=app_module.sha256_crypt.hash("pending-password"),
                role="teacher",
                report=0,
                emailed=0,
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
            "email": "validator@example.test",
            "password": "validator-password",
        },
    )
    assert login.status_code == 200

    response = client.post(
        "/validation/validate_user/pending-validation@example.test"
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User validated."}

    db = app_module.SessionLocal()
    try:
        assert db.query(app_module.NewUsers).filter_by(
            email="pending-validation@example.test"
        ).first() is None
        assert db.query(app_module.RegisteredUsers).filter_by(
            email="pending-validation@example.test"
        ).one()
    finally:
        db.close()
