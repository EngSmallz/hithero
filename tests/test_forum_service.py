import pytest

from backend.repositories.forum import ForumRepository
from backend.services.forum import ForumService


class RecordingRepository:
    def __init__(self):
        self.values = None

    def create_post(self, **values):
        self.values = values
        return values


def test_forum_service_sanitizes_post_fields_before_persistence():
    repository = RecordingRepository()
    service = ForumService(repository)

    result = service.create_post(
        title="<strong>Title</strong>",
        content="<p>Body</p>",
        user_id=42,
        sanitize=lambda value: value.replace("<", "[").replace(">", "]"),
    )

    assert result == repository.values
    assert repository.values == {
        "title": "[strong]Title[/strong]",
        "content": "[p]Body[/p]",
        "user_id": 42,
    }


class FailingSession:
    def __init__(self):
        self.rollback_called = False
        self.closed = False

    def add(self, _model):
        raise RuntimeError("post insert failed")

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.closed = True


def test_forum_repository_rolls_back_and_closes_failed_post_creation(app_module):
    session = FailingSession()
    repository = ForumRepository(
        session_factory=lambda: session,
        post_model=app_module.ForumPost,
    )

    with pytest.raises(RuntimeError, match="post insert failed"):
        repository.create_post(
            title="Title",
            content="Body",
            user_id=42,
        )

    assert session.rollback_called is True
    assert session.closed is True
