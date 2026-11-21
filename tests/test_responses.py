"""BE1-4: saved responses for every GET route, against the seeded database.

Each case calls one GET route as a given user (logged out, teacher or
admin) and compares status, redirect target, body and the session the
response leaves behind with tests/golden/responses/<case>.json.
Moving code between layers must not change what the pages receive.

Large static bodies (HTML pages, ads.txt, sitemap.xml) are stored as a
SHA-256 so the golden files stay readable.

After an intended change, regenerate with:
    UPDATE_GOLDEN=1 TEST_DATABASE=1 pytest tests/test_responses.py
and review the diff under tests/golden/responses/.
"""
import hashlib
import json
from pathlib import Path

import pytest

from tests import helpers
from tests.helpers import ADMIN, ALICE, ALICE_PAGE, BOB_PAGE, requires_db
from tests import testenv
from tests.testenv import update_golden

GOLDEN_DIR = Path(__file__).parent / "golden" / "responses"

SEEDED_TEACHERS = {"Alice Adams", "Bob Brown", "Carol Cruz"}


@pytest.fixture(scope="module", autouse=True)
def seeded_db():
    """Golden responses assume the seed data. Write tests that ran earlier
    (test_flows.py) leave the database changed, so reseed first."""
    if helpers.db_dirty and testenv.use_database():
        helpers.reseed()
        helpers.db_dirty = False

# (case name, session before the call, GET paths called in order).
# Only the last call is recorded; earlier ones set up the session.
CASES = [
    ("root", None, ["/"]),
    ("ads_txt", None, ["/ads.txt"]),
    ("sitemap_xml", None, ["/sitemap.xml"]),
    ("get_states", None, ["/api/get_states/"]),
    ("get_counties", None, ["/api/get_counties/Illinois"]),
    ("get_counties_none", None, ["/api/get_counties/Nowhere"]),
    ("get_districts", None, ["/api/get_districts/Illinois/Sangamon"]),
    ("get_districts_none", None, ["/api/get_districts/Illinois/Nowhere"]),
    ("get_schools", None, ["/api/get_schools/Illinois/Sangamon/Springfield District"]),
    ("get_schools_none", None, ["/api/get_schools/Illinois/Sangamon/Nowhere"]),
    ("index_states", None, ["/api/index_states/"]),
    ("index_counties", None, ["/api/index_counties/Illinois"]),
    ("index_counties_none", None, ["/api/index_counties/Nowhere"]),
    ("index_districts", None, ["/api/index_districts/Illinois/Sangamon"]),
    ("index_districts_none", None, ["/api/index_districts/Illinois/Nowhere"]),
    ("index_schools", None, ["/api/index_schools/Illinois/Sangamon/Springfield District"]),
    ("index_schools_none", None, ["/api/index_schools/Illinois/Sangamon/Nowhere"]),
    ("teacher_of_the_day", None, ["/api/teacher_of_the_day"]),
    ("random_teacher", None, ["/api/random_teacher/"]),
    ("teacher_page", None, ["/teacher/alice1234"]),
    ("teacher_page_missing", None, ["/teacher/nobody"]),
    ("teacher_info_no_session", None, ["/api/get_teacher_info/"]),
    ("teacher_info", ALICE_PAGE, ["/api/get_teacher_info/"]),
    ("teacher_url", ALICE_PAGE, ["/api/teacher_url/"]),
    ("teacher_url_no_session", None, ["/api/teacher_url/"]),
    ("forum_posts", None, ["/forum/get_posts"]),
    ("forum_post", None, ["/forum/get_post?post_id=1"]),
    ("forum_post_missing", None, ["/forum/get_post?post_id=999"]),
    ("forum_comments", None, ["/forum/comments/1/"]),
    ("forum_comments_missing", None, ["/forum/comments/999/"]),
    ("promo_info_empty", None, ["/promo/get_promo_info/"]),
    ("promo_token", None, ["/seattlewolf"]),
    ("promo_info_after_token", None, ["/seattlewolf", "/promo/get_promo_info/"]),
    ("promo_unknown_token", None, ["/notapartner"]),
    ("profile_logged_out", None, ["/api/profile/"]),
    ("profile_teacher", ALICE, ["/api/profile/"]),
    ("profile_admin", ADMIN, ["/api/profile/"]),
    ("myinfo_logged_out", None, ["/profile/myinfo/"]),
    ("myinfo_teacher", ALICE, ["/profile/myinfo/"]),
    ("myinfo_admin", ADMIN, ["/profile/myinfo/"]),
    ("check_access_logged_out", ALICE_PAGE, ["/api/check_access_teacher/"]),
    ("check_access_own_page", {**ALICE, **ALICE_PAGE}, ["/api/check_access_teacher/"]),
    ("check_access_other_page", {**ALICE, **BOB_PAGE}, ["/api/check_access_teacher/"]),
    ("check_access_admin", {**ADMIN, **ALICE_PAGE}, ["/api/check_access_teacher/"]),
    ("validation_list_logged_out", None, ["/api/validation_list/"]),
    ("validation_list_teacher", ALICE, ["/api/validation_list/"]),
    ("validation_list_admin", ADMIN, ["/api/validation_list/"]),
]


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def record(response, session: dict) -> dict:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        body = response.json()
    elif content_type.startswith("text/plain") and len(response.content) < 2000:
        body = response.text
    else:
        body = _digest(response.content)
    result = {
        "status": response.status_code,
        "content_type": content_type,
        "location": response.headers.get("location"),
        "body": body,
        "session": session,
    }
    return result


def normalize(name: str, result: dict) -> dict:
    # NEWID() picks any teacher: check it is a seeded one, then fix the
    # value so the golden file stays stable.
    if name == "random_teacher" and result["status"] == 200:
        assert result["body"]["name"] in SEEDED_TEACHERS
        for key in ("name", "state", "county", "district", "school"):
            result["body"][key] = f"<random teacher {key}>"
            if key in result["session"] or key == "name":
                session_key = "teacher" if key == "name" else key
                result["session"][session_key] = f"<random teacher {key}>"
    return result


@requires_db
@pytest.mark.parametrize("name,session,paths", CASES, ids=[c[0] for c in CASES])
def test_get_response_matches_golden(name, session, paths):
    c = helpers.client(session)
    for path in paths:
        response = c.get(path)
    actual = normalize(name, record(response, helpers.session_of(c)))

    golden = GOLDEN_DIR / f"{name}.json"
    if update_golden():
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
    expected = json.loads(golden.read_text())
    assert actual == expected, f"Response for {name} differs from {golden.name}"


def test_every_get_route_has_a_case():
    """A new GET route should get a golden case too."""
    routes = (Path(__file__).parent / "golden" / "routes.txt").read_text().splitlines()
    get_routes = {line.split(" ", 1)[1] for line in routes if line.startswith("GET ")}
    covered = {
        "/": "root", "/ads.txt": "ads_txt", "/sitemap.xml": "sitemap_xml",
        "/api/get_states/": "get_states", "/api/get_counties/{state}": "get_counties",
        "/api/get_districts/{state}/{county}": "get_districts",
        "/api/get_schools/{state}/{county}/{district}": "get_schools",
        "/api/index_states/": "index_states", "/api/index_counties/{state}": "index_counties",
        "/api/index_districts/{state}/{county}": "index_districts",
        "/api/index_schools/{state}/{county}/{district}": "index_schools",
        "/api/teacher_of_the_day": "teacher_of_the_day",
        "/api/random_teacher/": "random_teacher", "/teacher/{url_id}": "teacher_page",
        "/api/get_teacher_info/": "teacher_info", "/api/teacher_url/": "teacher_url",
        "/forum/get_posts": "forum_posts", "/forum/get_post": "forum_post",
        "/forum/comments/{post_id}/": "forum_comments",
        "/promo/get_promo_info/": "promo_info_empty", "/{token}": "promo_token",
        "/api/profile/": "profile_teacher", "/profile/myinfo/": "myinfo_teacher",
        "/api/check_access_teacher/": "check_access_own_page",
        "/api/validation_list/": "validation_list_admin",
    }
    case_names = {c[0] for c in CASES}
    assert get_routes == set(covered), sorted(get_routes ^ set(covered))
    assert set(covered.values()) <= case_names
