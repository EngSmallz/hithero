from fastapi.testclient import TestClient
from sqlalchemy import delete


def seed_teacher_directory(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.TeacherList))
        db.add_all(
            [
                app_module.TeacherList(
                    name="Alice Adams",
                    state="WA",
                    county="King",
                    district="Seattle Public Schools",
                    school="Lincoln High School",
                    regUserID=1,
                    wishlist_url="https://example.test/alice",
                    about_me="Science supplies",
                    url_id="alice-adams",
                ),
                app_module.TeacherList(
                    name="Ben Baker",
                    state="WA",
                    county="Snohomish",
                    district="Everett Public Schools",
                    school="Everett High School",
                    regUserID=2,
                    wishlist_url="https://example.test/ben",
                    about_me="Art supplies",
                    url_id="ben-baker",
                ),
                app_module.TeacherList(
                    name="Carla Cruz",
                    state="OR",
                    county="Multnomah",
                    district="Portland Public Schools",
                    school="Grant High School",
                    regUserID=3,
                    wishlist_url="https://example.test/carla",
                    about_me="Classroom books",
                    url_id="carla-cruz",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def seed_school_options(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.School))
        db.add_all(
            [
                app_module.School(
                    school_name="Lincoln High School",
                    district="Seattle Public Schools",
                    county="King",
                    state="WA",
                ),
                app_module.School(
                    school_name="Everett High School",
                    district="Everett Public Schools",
                    county="Snohomish",
                    state="WA",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_teacher_directory_api_returns_filters_and_teacher_summaries(app_module):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    response = client.get("/api/teachers/")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [teacher["name"] for teacher in body["teachers"]] == [
        "Alice Adams",
        "Ben Baker",
        "Carla Cruz",
    ]
    assert body["teachers"][0] == {
        "name": "Alice Adams",
        "url_id": "alice-adams",
        "state": "WA",
        "county": "King",
        "district": "Seattle Public Schools",
        "school": "Lincoln High School",
    }
    assert body["filters"]["states"] == ["OR", "WA"]
    assert body["filters"]["counties"] == ["King", "Multnomah", "Snohomish"]


def test_teacher_directory_api_applies_location_filters(app_module):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    response = client.get(
        "/api/teachers/",
        params={
            "state": "WA",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Lincoln High School",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["teachers"][0]["name"] == "Alice Adams"
    assert body["filters"]["states"] == ["OR", "WA"]
    assert body["filters"]["counties"] == ["King", "Snohomish"]
    assert body["filters"]["districts"] == ["Seattle Public Schools"]
    assert body["filters"]["schools"] == ["Lincoln High School"]
    assert body["applied_filters"] == {
        "state": "WA",
        "county": "King",
        "district": "Seattle Public Schools",
        "school": "Lincoln High School",
    }


def test_teacher_directory_api_returns_empty_list_for_no_matches(app_module):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    response = client.get("/api/teachers/", params={"state": "AK"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["teachers"] == []
    assert body["applied_filters"]["state"] == "AK"


def test_teacher_directory_api_paginates_without_truncating_total(app_module):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    response = client.get(
        "/api/teachers/",
        params={"page": 2, "page_size": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 2
    assert body["page_size"] == 2
    assert body["total_pages"] == 2
    assert [teacher["name"] for teacher in body["teachers"]] == ["Carla Cruz"]


def test_teacher_directory_api_skips_profiles_without_shareable_urls(app_module):
    seed_teacher_directory(app_module)
    db = app_module.SessionLocal()
    try:
        db.add(
            app_module.TeacherList(
                name="Legacy Teacher",
                state="WA",
                county="King",
                district="Seattle Public Schools",
                school="Legacy School",
                regUserID=4,
                url_id=None,
            )
        )
        db.commit()
    finally:
        db.close()

    response = TestClient(app_module.app).get("/api/teachers/")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert all(teacher["url_id"] for teacher in response.json()["teachers"])


def test_public_teacher_profile_api_returns_profile_by_url_id(app_module):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    response = client.get("/api/teacher/alice-adams/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice Adams",
        "url_id": "alice-adams",
        "state": "WA",
        "county": "King",
        "district": "Seattle Public Schools",
        "school": "Lincoln High School",
        "wishlist_url": "https://example.test/alice",
        "about_me": "Science supplies",
        "image_data": None,
    }


def test_public_teacher_profile_api_returns_404_for_unknown_url_id(app_module):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    response = client.get("/api/teacher/not-a-teacher/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Teacher not found"


def test_session_selected_teacher_endpoints_preserve_not_found_and_forbidden_statuses(
    app_module,
):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    teacher_info = client.get("/api/get_teacher_info/")
    teacher_url = client.get("/api/teacher_url/")
    edit_access = client.get("/api/check_access_teacher/")

    assert teacher_info.status_code == 404
    assert teacher_url.status_code == 404
    assert edit_access.status_code == 403


def test_random_teacher_preserves_not_found_status(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.TeacherList))
        db.commit()
    finally:
        db.close()

    response = TestClient(app_module.app).get("/api/random_teacher/")

    assert response.status_code == 404


def test_teacher_directory_option_and_index_routes_preserve_legacy_contracts(
    app_module,
):
    seed_teacher_directory(app_module)
    seed_school_options(app_module)
    client = TestClient(app_module.app)

    assert client.get("/api/get_states/").json() == ["WA"]
    assert client.get("/api/get_counties/WA").json() == ["King", "Snohomish"]
    assert client.get("/api/get_districts/WA/King").json() == [
        "Seattle Public Schools"
    ]
    assert client.get("/api/get_schools/WA/King/Seattle%20Public%20Schools").json() == [
        "Lincoln High School"
    ]

    assert client.get("/api/index_states/").json() == ["OR", "WA"]
    assert client.get("/api/index_counties/WA").json() == ["King", "Snohomish"]
    assert client.get("/api/index_districts/WA/King").json() == [
        "Seattle Public Schools"
    ]
    assert client.get(
        "/api/index_schools/WA/King/Seattle%20Public%20Schools"
    ).json() == ["Lincoln High School"]

    response = client.post("/api/index_teachers/", data={"state": "WA", "county": "King"})
    assert response.status_code == 200
    assert response.json() == [{"name": "Alice Adams", "url_id": "alice-adams"}]


def test_teacher_directory_option_and_index_routes_preserve_not_found_messages(
    app_module,
):
    seed_teacher_directory(app_module)
    client = TestClient(app_module.app)

    assert client.get("/api/get_counties/AK").json() == {
        "message": "No counties found for state: AK"
    }
    assert client.get("/api/index_districts/AK/Unknown").json() == {
        "message": "No districts found for state: AK and county: Unknown"
    }
    response = client.post("/api/index_teachers/", data={"state": "AK"})
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "Page Does Not Exist" in response.text
