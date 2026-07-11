import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.db.models import TeacherList
from backend.repositories.profile import ProfileRepository
from backend.services.profile_mutations import (
    InvalidTeacherUrlId,
    ProfileMutationService,
    TeacherUrlIdConflict,
)


class RecordingRepository:
    def update_teacher_school(self, user_id, **values):
        self.user_id = user_id
        self.values = values

    def update_teacher_name(self, user_id, name):
        self.name_update = (user_id, name)

    def update_teacher_wishlist(self, user_id, wishlist_url):
        self.wishlist_update = (user_id, wishlist_url)

    def get_teacher_by_url_id(self, url_id):
        self.url_id_lookup = url_id
        return getattr(self, "existing_teacher", None)

    def update_teacher_url_id(self, user_id, url_id):
        self.url_id_update = (user_id, url_id)


def test_profile_mutation_service_passes_school_update_as_one_use_case():
    repository = RecordingRepository()
    service = ProfileMutationService(repository)

    service.update_teacher_school(
        42,
        state="IL",
        county="Cook",
        district="District 1",
        school="Example School",
    )

    assert repository.user_id == 42
    assert repository.values == {
        "state": "IL",
        "county": "Cook",
        "district": "District 1",
        "school": "Example School",
    }


def test_profile_mutation_service_preserves_name_and_wishlist_updates():
    repository = RecordingRepository()
    service = ProfileMutationService(repository)

    service.update_teacher_name(42, "Updated Teacher")
    service.update_teacher_wishlist(42, "https://example.test/list")

    assert repository.name_update == (42, "Updated Teacher")
    assert repository.wishlist_update == (
        42,
        "https://example.test/list&tag=h0mer00mher0-20",
    )


def test_profile_mutation_service_validates_and_updates_teacher_url_id():
    repository = RecordingRepository()
    service = ProfileMutationService(repository)

    service.update_teacher_url_id(42, "new-teacher_42")

    assert repository.url_id_lookup == "new-teacher_42"
    assert repository.url_id_update == (42, "new-teacher_42")


@pytest.mark.parametrize("url_id", ["no", "bad value", "bad/value", "a" * 51])
def test_profile_mutation_service_rejects_invalid_teacher_url_id(url_id):
    repository = RecordingRepository()
    service = ProfileMutationService(repository)

    with pytest.raises(InvalidTeacherUrlId):
        service.update_teacher_url_id(42, url_id)

    assert not hasattr(repository, "url_id_lookup")
    assert not hasattr(repository, "url_id_update")


def test_profile_mutation_service_rejects_teacher_url_id_collision():
    repository = RecordingRepository()
    repository.existing_teacher = object()
    service = ProfileMutationService(repository)

    with pytest.raises(TeacherUrlIdConflict):
        service.update_teacher_url_id(42, "existing-teacher")

    assert repository.url_id_lookup == "existing-teacher"
    assert not hasattr(repository, "url_id_update")


class FailingSession:
    def __init__(self):
        self.rollback_called = False
        self.closed = False

    def execute(self, _query):
        raise RuntimeError("write failed")

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.closed = True


def test_profile_repository_rolls_back_and_closes_failed_school_update():
    session = FailingSession()
    repository = ProfileRepository(
        session_factory=lambda: session,
        teacher_model=TeacherList,
    )

    with pytest.raises(RuntimeError, match="write failed"):
        repository.update_teacher_school(
            42,
            state="IL",
            county="Cook",
            district="District 1",
            school="Example School",
        )

    assert session.rollback_called is True
    assert session.closed is True


def test_profile_repository_rolls_back_and_closes_failed_url_id_update():
    session = FailingSession()
    repository = ProfileRepository(
        session_factory=lambda: session,
        teacher_model=TeacherList,
    )

    with pytest.raises(RuntimeError, match="write failed"):
        repository.update_teacher_url_id(42, "new-teacher")

    assert session.rollback_called is True
    assert session.closed is True


def seed_url_id_profiles(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.TeacherList))
        db.execute(delete(app_module.RegisteredUsers))
        user = app_module.RegisteredUsers(
            email="url-id-owner@example.test",
            phone_number="555-0142",
            password=app_module.sha256_crypt.hash("test-password"),
            role="teacher",
            createCount=1,
        )
        db.add(user)
        db.flush()
        db.add(
            app_module.TeacherList(
                name="URL ID Owner",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Lincoln High School",
                regUserID=user.id,
                url_id="owner-teacher",
            )
        )
        db.add(
            app_module.TeacherList(
                name="Other Teacher",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Roosevelt High School",
                regUserID=999,
                url_id="taken-teacher",
            )
        )
        db.commit()
    finally:
        db.close()


def login_url_id_user(client):
    response = client.post(
        "/profile/login/",
        data={
            "email": "url-id-owner@example.test",
            "password": "test-password",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "teacher"


def test_update_url_id_api_preserves_validation_collision_and_success_contracts(
    app_module,
):
    seed_url_id_profiles(app_module)
    client = TestClient(app_module.app)
    login_url_id_user(client)

    invalid = client.post(
        "/profile/update_url_id/",
        data={"url_id": "bad value"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == (
        "URL ID may only contain letters, numbers, hyphens, and underscores "
        "(3–50 characters)."
    )

    collision = client.post(
        "/profile/update_url_id/",
        data={"url_id": "taken-teacher"},
    )
    assert collision.status_code == 409
    assert collision.json()["detail"] == "URL ID already in use."

    updated = client.post(
        "/profile/update_url_id/",
        data={"url_id": "updated-teacher"},
    )
    assert updated.status_code == 200
    assert updated.json() == {"message": "URL ID updated successfully."}

    db = app_module.SessionLocal()
    try:
        assert db.query(app_module.TeacherList).filter_by(
            name="URL ID Owner", url_id="updated-teacher"
        ).one()
    finally:
        db.close()
