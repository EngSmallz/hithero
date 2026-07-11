import pytest

from backend.db.models import TeacherList
from backend.repositories.profile import ProfileRepository
from backend.services.profile_mutations import ProfileMutationService


class RecordingRepository:
    def update_teacher_school(self, user_id, **values):
        self.user_id = user_id
        self.values = values


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
