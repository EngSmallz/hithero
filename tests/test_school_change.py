from passlib.hash import sha256_crypt
from fastapi.testclient import TestClient
from sqlalchemy import delete


def seed_verified_teacher(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        for model in (
            app_module.SchoolChangeRequest,
            app_module.TeacherList,
            app_module.RegisteredUsers,
            app_module.School,
        ):
            db.execute(delete(model))

        user = app_module.RegisteredUsers(
            email="school-change@example.test",
            phone_number="555-0100",
            password=sha256_crypt.hash("school-password"),
            role="teacher",
            createCount=1,
            registration_name="School Change Teacher",
            registration_state="Washington",
            registration_county="King",
            registration_district="Seattle Public Schools",
            registration_school="Evergreen Elementary",
        )
        db.add(user)
        db.add_all(
            [
                app_module.School(
                    school_name="Evergreen Elementary",
                    district="Seattle Public Schools",
                    county="King",
                    state="Washington",
                ),
                app_module.School(
                    school_name="Roosevelt High School",
                    district="Seattle Public Schools",
                    county="King",
                    state="Washington",
                ),
                app_module.School(
                    school_name="Lincoln High School",
                    district="Seattle Public Schools",
                    county="King",
                    state="Washington",
                ),
            ]
        )
        db.flush()
        db.add(
            app_module.TeacherList(
                name="School Change Teacher",
                state="Washington",
                county="King",
                district="Seattle Public Schools",
                school="Evergreen Elementary",
                regUserID=user.id,
                url_id="school-change-teacher",
            )
        )
        db.commit()
    finally:
        db.close()


def login_school_change_teacher(app_module):
    app_module.app.state.limiter._storage.reset()
    client = TestClient(app_module.app)
    response = client.post(
        "/profile/login/",
        data={
            "email": "school-change@example.test",
            "password": "school-password",
        },
    )
    assert response.status_code == 200
    return client


def test_school_change_requires_confirmation_and_hides_pending_profile(app_module):
    seed_verified_teacher(app_module)
    client = login_school_change_teacher(app_module)

    unconfirmed = client.post(
        "/profile/request_school_change/",
        data={
            "state": "Washington",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Roosevelt High School",
        },
    )
    assert unconfirmed.status_code == 400

    submitted = client.post(
        "/profile/request_school_change/",
        data={
            "state": "Washington",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Roosevelt High School",
            "confirm_school_change": "true",
        },
    )
    assert submitted.status_code == 200
    assert submitted.json() == {"message": "School change submitted for reapproval."}

    db = app_module.SessionLocal()
    try:
        teacher = db.query(app_module.TeacherList).one()
        request = db.query(app_module.SchoolChangeRequest).one()
        assert teacher.school == "Evergreen Elementary"
        assert teacher.school_change_pending == 1
        assert request.status == "pending"
        assert request.old_school == "Evergreen Elementary"
        assert request.proposed_school == "Roosevelt High School"
    finally:
        db.close()

    assert client.get("/api/teachers/").json()["total"] == 0
    assert client.get("/api/teacher/school-change-teacher/").status_code == 404

    validation = client.get("/api/validation_list/")
    assert validation.status_code == 200
    assert validation.json()["school_changes"] == [
        {
            "id": request.id,
            "user_id": request.user_id,
            "old": {
                "state": "Washington",
                "county": "King",
                "district": "Seattle Public Schools",
                "school": "Evergreen Elementary",
            },
            "proposed": {
                "state": "Washington",
                "county": "King",
                "district": "Seattle Public Schools",
                "school": "Roosevelt High School",
            },
            "status": "pending",
            "created_at": request.created_at.isoformat(),
        }
    ]


def test_school_change_approval_and_rejection_preserve_verification_safety(app_module):
    seed_verified_teacher(app_module)
    client = login_school_change_teacher(app_module)

    first = client.post(
        "/profile/request_school_change/",
        data={
            "state": "Washington",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Roosevelt High School",
            "confirm_school_change": "true",
        },
    )
    assert first.status_code == 200
    db = app_module.SessionLocal()
    try:
        request_id = db.query(app_module.SchoolChangeRequest).one().id
    finally:
        db.close()

    approved = client.post(
        f"/validation/school_change/{request_id}/approved"
    )
    assert approved.status_code == 200

    db = app_module.SessionLocal()
    try:
        teacher = db.query(app_module.TeacherList).one()
        registered = db.query(app_module.RegisteredUsers).one()
        request = db.query(app_module.SchoolChangeRequest).one()
        assert teacher.school == "Roosevelt High School"
        assert teacher.school_change_pending == 0
        assert registered.registration_school == "Roosevelt High School"
        assert request.status == "approved"
    finally:
        db.close()
    assert client.get("/api/teacher/school-change-teacher/").status_code == 200

    second = client.post(
        "/profile/request_school_change/",
        data={
            "state": "Washington",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Lincoln High School",
            "confirm_school_change": "true",
        },
    )
    assert second.status_code == 200
    db = app_module.SessionLocal()
    try:
        second_id = (
            db.query(app_module.SchoolChangeRequest)
            .filter_by(status="pending")
            .one()
            .id
        )
    finally:
        db.close()

    rejected = client.post(f"/validation/school_change/{second_id}/rejected")
    assert rejected.status_code == 200

    db = app_module.SessionLocal()
    try:
        teacher = db.query(app_module.TeacherList).one()
        registered = db.query(app_module.RegisteredUsers).one()
        request = (
            db.query(app_module.SchoolChangeRequest)
            .filter_by(id=second_id)
            .one()
        )
        assert teacher.school == "Roosevelt High School"
        assert teacher.school_change_pending == 0
        assert registered.registration_school == "Roosevelt High School"
        assert request.status == "rejected"
    finally:
        db.close()
