from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.forum import create_forum_router
from backend.core.errors import DomainError, domain_error_handler


class NoopLimiter:
    def limit(self, _limit):
        def decorator(endpoint):
            return endpoint

        return decorator


class SpyQuery:
    def __init__(self, session, model):
        self.session = session
        self.model = model

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        rows = self.session.rows.get(self.model, [])
        if not rows:
            return None
        return rows.pop(0)

    def all(self):
        return list(self.session.rows.get(self.model, []))


class SpySession:
    def __init__(self, rows):
        self.rows = {model: list(values) for model, values in rows.items()}
        self.events = []

    def query(self, model):
        self.events.append("query")
        return SpyQuery(self, model)

    def add(self, _record):
        self.events.append("add")

    def delete(self, _record):
        self.events.append("delete")

    def commit(self):
        self.events.append("commit")

    def refresh(self, _record):
        self.events.append("refresh")

    def rollback(self):
        self.events.append("rollback")

    def close(self):
        self.events.append("close")


def make_record(**values):
    defaults = {
        "id": 1,
        "title": "Forum post",
        "content": "Forum content",
        "post_id": 1,
        "user_id": 10,
        "created_at": datetime(2026, 6, 26, 12, 0, 0),
        "upvote_count": 0,
        "comment_count": 0,
        "parent_comment_id": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def make_client(
    app_module,
    rows=None,
    *,
    current_user_id=10,
    role="teacher",
    session_factory_override=None,
):
    sessions = []

    def session_factory():
        if session_factory_override is not None:
            return session_factory_override()
        session = SpySession(rows or {})
        sessions.append(session)
        return session

    def model_to_dict(record):
        return {
            column.name: getattr(record, column.name)
            for column in record.__table__.columns
            if hasattr(record, column.name)
        }

    test_app = FastAPI()
    test_app.add_exception_handler(DomainError, domain_error_handler)
    test_app.include_router(
        create_forum_router(
            session_factory=session_factory,
            post_model=app_module.ForumPost,
            comment_model=app_module.ForumComment,
            vote_model=app_module.PostVote,
            vote_input_model=app_module.VoteInput,
            post_update_model=app_module.PostUpdate,
            get_current_id=lambda: current_user_id,
            get_current_role=lambda: role,
            limiter=NoopLimiter(),
            clean_html=app_module.bleach.clean,
            allowed_tags=app_module.ALLOWED_TAGS,
            allowed_attrs=app_module.ALLOWED_ATTRS,
            allowed_protocols=app_module.ALLOWED_PROTOCOLS,
            model_to_dict=model_to_dict,
        )
    )
    return TestClient(test_app), sessions


def test_unexpected_forum_errors_are_logged_and_return_non_sensitive_500(
    app_module, caplog
):
    class ExplodingSession:
        def query(self, _model):
            raise RuntimeError("database-password-should-not-leak")

        def close(self):
            pass

    client, _ = make_client(
        app_module,
        session_factory_override=ExplodingSession,
    )

    with caplog.at_level("ERROR", logger="backend.routers.forum"):
        response = client.get("/forum/get_posts")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Could not retrieve posts due to a server error."
    }
    assert "database-password-should-not-leak" not in response.text
    assert "Database error during post retrieval" in caplog.text


def assert_closed_once_with_rollback(session):
    assert session.events.count("rollback") == 1
    assert session.events.count("close") == 1
    assert session.events.index("rollback") < session.events.index("close")


def test_invalid_vote_type_rolls_back_and_closes_session(app_module):
    client, sessions = make_client(app_module)

    response = client.post("/forum/posts/1/vote", json={"vote_type": 2})

    assert response.status_code == 400
    assert_closed_once_with_rollback(sessions[0])


def test_vote_for_missing_post_rolls_back_and_closes_session(app_module):
    client, sessions = make_client(app_module)

    response = client.post("/forum/posts/404/vote", json={"vote_type": 1})

    assert response.status_code == 404
    assert_closed_once_with_rollback(sessions[0])


def test_comment_for_missing_parent_rolls_back_and_closes_session(app_module):
    client, sessions = make_client(
        app_module,
        rows={app_module.ForumPost: [make_record()]},
    )

    response = client.post(
        "/forum/posts/1/comment",
        data={"content": "Reply", "parent_comment_id": "404"},
    )

    assert response.status_code == 404
    assert_closed_once_with_rollback(sessions[0])


def test_comments_for_missing_post_closes_session(app_module):
    client, sessions = make_client(app_module)

    response = client.get("/forum/comments/404/")

    assert response.status_code == 404
    assert sessions[0].events.count("rollback") == 0
    assert sessions[0].events.count("close") == 1


def test_unauthorized_post_edit_rolls_back_and_closes_session(app_module):
    client, sessions = make_client(
        app_module,
        rows={app_module.ForumPost: [make_record(user_id=99)]},
    )

    response = client.patch(
        "/forum/post/1/update",
        json={"title": "Updated", "content": "Updated content"},
    )

    assert response.status_code == 403
    assert_closed_once_with_rollback(sessions[0])


def test_unauthorized_comment_delete_rolls_back_and_closes_session(app_module):
    client, sessions = make_client(
        app_module,
        rows={app_module.ForumComment: [make_record(user_id=99)]},
    )

    response = client.delete("/forum/comment/1/delete")

    assert response.status_code == 403
    assert_closed_once_with_rollback(sessions[0])


def test_unauthorized_comment_edit_rolls_back_and_closes_session(app_module):
    client, sessions = make_client(
        app_module,
        rows={app_module.ForumComment: [make_record(user_id=99)]},
    )

    response = client.patch(
        "/forum/comment/1/update",
        data={"content": "Attempted update"},
    )

    assert response.status_code == 403
    assert_closed_once_with_rollback(sessions[0])


def test_non_admin_post_delete_is_rejected_before_deletion(app_module):
    client, sessions = make_client(
        app_module,
        rows={app_module.ForumPost: [make_record(user_id=10)]},
        role="teacher",
    )

    response = client.delete("/forum/post/1/delete")

    assert response.status_code == 403
    assert sessions == []
