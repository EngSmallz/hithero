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
