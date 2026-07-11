from types import SimpleNamespace

import app
from backend.core import auth


class RequestStub:
    def __init__(self, session=None):
        self.session = {} if session is None else session


def test_session_readers_preserve_legacy_values_and_missing_keys():
    request = RequestStub(
        {
            "user_id": 42,
            "user_role": "teacher",
            "user_email": "teacher@example.test",
            "state": "IL",
        }
    )

    assert auth.get_current_id(request) == 42
    assert auth.get_current_role(request) == "teacher"
    assert auth.get_current_email(request) == "teacher@example.test"
    assert auth.get_index_cookie("state", request) == "IL"
    assert auth.get_index_cookie("missing", request) is None


def test_teacher_session_writer_preserves_legacy_directory_context():
    request = RequestStub()
    teacher = SimpleNamespace(
        state="IL",
        county="Cook",
        district="District 1",
        school="Example School",
        name="Example Teacher",
    )

    auth.set_teacher_session(request, teacher)

    assert request.session == {
        "state": "IL",
        "county": "Cook",
        "district": "District 1",
        "school": "Example School",
        "teacher": "Example Teacher",
    }


def test_app_reexports_auth_helpers_for_router_compatibility():
    assert app.get_current_id is auth.get_current_id
    assert app.get_current_role is auth.get_current_role
    assert app.get_current_email is auth.get_current_email
    assert app.get_index_cookie is auth.get_index_cookie
    assert app.set_teacher_session is auth.set_teacher_session
