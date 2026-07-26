import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.core.errors import ForbiddenError
from backend.core.policies import (
    AuthenticationRequired,
    require_admin,
    require_authenticated_user,
    require_forum_content_owner,
    require_owner,
    require_profile_owner,
    require_teacher_district_scope,
    require_teacher_or_admin,
)


def test_authenticated_policy_rejects_missing_session_identity():
    with pytest.raises(AuthenticationRequired) as error:
        require_authenticated_user(None, detail="Login required.")

    assert error.value.status_code == 401
    assert error.value.detail == "Login required."


def test_role_policies_reject_wrong_roles():
    with pytest.raises(ForbiddenError):
        require_admin("teacher")
    with pytest.raises(ForbiddenError):
        require_teacher_or_admin("user")


def test_owner_policy_rejects_missing_or_other_owner():
    with pytest.raises(ForbiddenError):
        require_owner(None, 42)
    with pytest.raises(ForbiddenError):
        require_owner(7, 42)
    with pytest.raises(ForbiddenError):
        require_forum_content_owner(False)
    with pytest.raises(ForbiddenError):
        require_profile_owner(7, 42)
    with pytest.raises(ForbiddenError):
        require_teacher_district_scope(False)


def test_role_and_owner_policies_return_authorized_values():
    assert require_authenticated_user(42) == 42
    assert require_admin("admin") == "admin"
    assert require_teacher_or_admin("teacher") == "teacher"
    assert require_owner(42, 42) == 42
    assert require_forum_content_owner(True) is True
    assert require_profile_owner(42) == 42
    assert require_teacher_district_scope(True) is True


def test_forum_mutations_reject_unauthenticated_requests_before_database_access(
    app_module,
):
    client = TestClient(app_module.app)

    for response in (
        client.post(
            "/forum/create_post",
            data={"title": "Title", "content": "Body"},
        ),
        client.post("/forum/posts/1/vote", json={"vote_type": 1}),
        client.post("/forum/posts/1/comment", data={"content": "Body"}),
        client.delete("/forum/comment/1/delete"),
        client.patch(
            "/forum/post/1/update",
            json={"title": "Title", "content": "Body"},
        ),
        client.patch(
            "/forum/comment/1/update",
            data={"content": "Body"},
        ),
    ):
        assert response.status_code == 401

    assert client.delete("/forum/post/1/delete").status_code == 403


def test_privileged_admin_and_profile_mutations_reject_wrong_roles(app_module):
    client = TestClient(app_module.app)

    admin_response = client.post(
        "/validation/delete_user/pending@example.test",
    )
    profile_response = client.post(
        "/profile/update_info/",
        data={"aboutMe": "Attempted update"},
    )
    myinfo_response = client.get("/profile/myinfo/")

    assert admin_response.status_code == 403
    assert profile_response.status_code == 403
    assert myinfo_response.status_code == 401


def test_profile_creation_rejects_unauthenticated_requests(app_module):
    response = TestClient(app_module.app).post(
        "/profile/create_teacher_profile/",
        data={
            "name": "Unauthorized Teacher",
            "state": "WA",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Lincoln High School",
            "aboutMe": "Attempted profile",
            "wishlist": "https://example.test/list",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "You must be logged in to create a teacher profile."
    }


def seed_and_login_basic_user(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.RegisteredUsers))
        db.add(
            app_module.RegisteredUsers(
                email="wrong-role@example.test",
                phone_number="555-0102",
                password=app_module.sha256_crypt.hash("user-password"),
                role="user",
                createCount=0,
            )
        )
        db.commit()
    finally:
        db.close()

    app_module.app.state.limiter._storage.reset()
    client = TestClient(app_module.app)
    assert client.post(
        "/profile/login/",
        data={"email": "wrong-role@example.test", "password": "user-password"},
    ).status_code == 200
    return client


def test_profile_creation_rejects_authenticated_wrong_role(app_module):
    response = seed_and_login_basic_user(app_module).post(
        "/profile/create_teacher_profile/",
        data={
            "name": "Wrong Role",
            "state": "WA",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Lincoln High School",
            "aboutMe": "Attempted profile",
            "wishlist": "https://example.test/list",
        },
    )

    assert response.status_code == 403


def test_password_update_rejects_unauthenticated_requests(app_module):
    response = TestClient(app_module.app).post(
        "/profile/update_password/",
        data={
            "old_password": "old-password",
            "new_password": "new-password",
            "new_password_confirmed": "new-password",
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "path",
    (
        "/internal/run-wednesday-job",
        "/internal/run-tuesday-job",
        "/internal/run-thursday-job",
        "/internal/run-daily-job",
    ),
)
def test_internal_job_mutations_reject_unauthenticated_requests(app_module, path):
    assert TestClient(app_module.app).post(path).status_code in {401, 403}


def test_rate_limits_cover_only_the_audited_abuse_sensitive_mutations(app_module):
    assert set(app_module.app.state.limiter._route_limits) == {
        "backend.routers.profile.register_user",
        "backend.routers.profile.login_user",
        "backend.routers.profile.forgot_password",
        "backend.routers.forum.create_post",
        "backend.routers.forum.add_comment_to_post",
    }


def test_login_rate_limit_is_enforced_with_429(app_module):
    app_module.app.state.limiter._storage.reset()
    client = TestClient(app_module.app)

    responses = [
        client.post(
            "/profile/login/",
            data={"email": "missing@example.test", "password": "wrong"},
        )
        for _ in range(6)
    ]

    assert all(response.status_code != 429 for response in responses[:5])
    assert responses[5].status_code == 429


PROFILE_MUTATIONS = (
    ("/profile/update_info/", {"aboutMe": "Updated"}),
    (
        "/profile/update_teacher_school/",
        {
            "state": "WA",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Lincoln High School",
        },
    ),
    ("/profile/update_teacher_name/", {"teacher": "Updated Name"}),
    ("/profile/update_wishlist/", {"wishlist": "https://example.test/list"}),
    ("/profile/update_url_id/", {"url_id": "updated-id"}),
)


@pytest.mark.parametrize(("path", "data"), PROFILE_MUTATIONS)
def test_profile_mutations_reject_unauthenticated_and_wrong_role(
    app_module, path, data
):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.RegisteredUsers))
        db.add(
            app_module.RegisteredUsers(
                email="basic-user@example.test",
                phone_number="555-0100",
                password=app_module.sha256_crypt.hash("user-password"),
                role="user",
                createCount=0,
            )
        )
        db.commit()
    finally:
        db.close()

    app_module.app.state.limiter._storage.reset()
    anonymous = TestClient(app_module.app)
    assert anonymous.post(path, data=data).status_code == 403

    basic_user = TestClient(app_module.app)
    login = basic_user.post(
        "/profile/login/",
        data={"email": "basic-user@example.test", "password": "user-password"},
    )
    assert login.status_code == 200
    assert basic_user.post(path, data=data).status_code == 403


def test_teacher_image_mutation_rejects_unauthenticated_and_wrong_role(app_module):
    app_module.init_db()
    db = app_module.SessionLocal()
    try:
        db.execute(delete(app_module.RegisteredUsers))
        db.add(
            app_module.RegisteredUsers(
                email="image-user@example.test",
                phone_number="555-0101",
                password=app_module.sha256_crypt.hash("user-password"),
                role="user",
                createCount=0,
            )
        )
        db.commit()
    finally:
        db.close()

    upload = {"image": ("teacher.png", b"not-an-image", "image/png")}
    anonymous = TestClient(app_module.app)
    assert anonymous.post("/profile/update_teacher_image/", files=upload).status_code == 403

    basic_user = TestClient(app_module.app)
    assert basic_user.post(
        "/profile/login/",
        data={"email": "image-user@example.test", "password": "user-password"},
    ).status_code == 200
    assert basic_user.post("/profile/update_teacher_image/", files=upload).status_code == 403


@pytest.mark.parametrize(
    "path",
    (
        "/validation/validate_user/pending@example.test",
        "/validation/delete_user/pending@example.test",
        "/validation/report_user/pending@example.test",
        "/validation/emailed_user/pending@example.test",
        "/admin/generate_teacher_report/",
        "/profile/delete/",
    ),
)
def test_admin_and_validation_mutations_reject_unauthenticated_requests(
    app_module, path
):
    response = TestClient(app_module.app).post(
        path,
        data={
            "state": "WA",
            "target_email": "target@example.test",
            "admin_secret_input": "invalid",
        },
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "path",
    (
        "/validation/validate_user/pending@example.test",
        "/validation/delete_user/pending@example.test",
        "/validation/report_user/pending@example.test",
        "/validation/emailed_user/pending@example.test",
        "/admin/generate_teacher_report/",
        "/profile/delete/",
    ),
)
def test_admin_and_validation_mutations_reject_authenticated_wrong_role(
    app_module, path
):
    response = seed_and_login_basic_user(app_module).post(
        path,
        data={
            "state": "WA",
            "target_email": "target@example.test",
            "admin_secret_input": "invalid",
        },
    )

    assert response.status_code == 403
