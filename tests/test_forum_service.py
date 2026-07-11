import pytest

from backend.repositories.forum import ForumRepository
from backend.services.forum import ForumService


class RecordingRepository:
    def __init__(self):
        self.values = None

    def create_post(self, **values):
        self.values = values
        return values

    def create_comment(self, **values):
        self.comment_values = values
        return "comment", None

    def record_vote(self, **values):
        self.vote_values = values
        return "post"


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


def test_forum_service_sanitizes_comments_and_delegates_votes():
    repository = RecordingRepository()
    service = ForumService(repository)
    sanitize = lambda value: value.strip()

    assert service.create_comment(
        post_id=1,
        user_id=42,
        content=" comment ",
        parent_comment_id=None,
        sanitize=sanitize,
    ) == "comment"
    assert repository.comment_values == {
        "post_id": 1,
        "user_id": 42,
        "content": "comment",
        "parent_comment_id": None,
    }

    assert service.record_vote(post_id=1, user_id=42, vote_type=1) == "post"
    assert repository.vote_values == {
        "post_id": 1,
        "user_id": 42,
        "vote_type": 1,
    }


def test_forum_service_maps_missing_comment_records_and_posts():
    class MissingRepository(RecordingRepository):
        def create_comment(self, **_values):
            return None, "parent"

        def record_vote(self, **_values):
            return None

    service = ForumService(MissingRepository())
    with pytest.raises(LookupError, match="Parent comment with ID 9 not found"):
        service.create_comment(
            post_id=1,
            user_id=42,
            content="Reply",
            parent_comment_id=9,
            sanitize=lambda value: value,
        )
    with pytest.raises(LookupError, match="Post with ID 1 not found"):
        service.record_vote(post_id=1, user_id=42, vote_type=1)


class FailingSession:
    def __init__(self):
        self.rollback_called = False
        self.closed = False

    def add(self, _model):
        raise RuntimeError("post insert failed")

    def query(self, _model):
        raise RuntimeError("forum query failed")

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


def test_forum_repository_rolls_back_and_closes_failed_comment_and_vote(app_module):
    session = FailingSession()
    repository = ForumRepository(
        session_factory=lambda: session,
        post_model=app_module.ForumPost,
        comment_model=app_module.ForumComment,
        vote_model=app_module.PostVote,
    )

    with pytest.raises(RuntimeError, match="forum query failed"):
        repository.create_comment(
            post_id=1,
            user_id=42,
            content="Reply",
            parent_comment_id=None,
        )
    assert session.rollback_called is True
    assert session.closed is True

    session = FailingSession()
    repository = ForumRepository(
        session_factory=lambda: session,
        post_model=app_module.ForumPost,
        comment_model=app_module.ForumComment,
        vote_model=app_module.PostVote,
    )
    with pytest.raises(RuntimeError, match="forum query failed"):
        repository.record_vote(post_id=1, user_id=42, vote_type=1)
    assert session.rollback_called is True
    assert session.closed is True
