"""BE1-6: flow tests for the write paths.

Golden files cover reads; these walk the main write journeys end to end
through the HTTP API, each on a freshly seeded database:
  - register > validate > login > create profile > open the teacher page
  - forgot password > reset > log in with the new password
  - forum post > comment > vote > edit > delete

They assert today's behaviour, including responses that look wrong
(noted inline), so the refactor can't change them silently. When a
later task fixes one of those on purpose, update the assertion with it.
"""
import re

import pytest

from tests import helpers
from tests.helpers import fresh_db, outbox, requires_db  # noqa: F401  (fixtures)
from tests.seed import SEED_PASSWORD

pytestmark = requires_db


def login(c, email, password=SEED_PASSWORD):
    return c.post("/profile/login/", data={"email": email, "password": password})


def test_register_validate_create_profile(fresh_db):
    outbox = fresh_db
    new = {
        "name": "Dana Diaz", "email": "dana@example.com", "phone_number": "5551112222",
        "password": "Dana-Passw0rd!", "confirm_password": "Dana-Passw0rd!",
        "state": "Illinois", "county": "Sangamon", "district": "Springfield District",
        "school": "Douglas Middle", "recaptcha_response": "ok",
    }

    # Register: goes into the validation queue and gets an email.
    visitor = helpers.client()
    r = visitor.post("/profile/register/", data=new)
    assert r.status_code == 200
    assert r.json()["message"].startswith("User registered successfully")
    assert outbox.sent[-1]["content"]["subject"] == "Registration successful"

    r = visitor.post("/profile/register/", data=new)
    assert r.json() == {"message": "User with this email is already in the registration queue."}

    # Not validated yet: can't log in.
    r = login(visitor, new["email"], new["password"])
    assert r.json() == {"message": "Invalid login credentials."}

    # A teacher in another district can't validate.
    carol = helpers.client()
    login(carol, "carol@example.com")
    r = carol.post(f"/validation/validate_user/{new['email']}")
    assert r.status_code == 403

    # A teacher in the same district can.
    alice = helpers.client()
    login(alice, "alice@example.com")
    r = alice.get("/api/validation_list/")
    assert new["email"] in [u["email"] for u in r.json()["new_users"]]
    r = alice.post(f"/validation/validate_user/{new['email']}")
    assert r.status_code == 200
    assert r.json() == {"message": "User validated."}
    assert outbox.sent[-1]["content"]["subject"] == "Validation Notification"

    # Log in and create the teacher profile.
    dana = helpers.client()
    r = login(dana, new["email"], new["password"])
    assert r.json() == {"message": "Login successful as teacher", "createCount": None, "role": "teacher"}
    # createCount is NULL for validated users: move_user doesn't set it, and
    # create_teacher_profile only allows createCount == 0 for teachers.
    r = dana.post("/profile/create_teacher_profile/", data={
        "name": "Dana Diaz", "state": "Illinois", "county": "Sangamon",
        "district": "Springfield District", "school": "Douglas Middle",
        "aboutMe": "Music teacher.", "wishlist": "https://www.amazon.com/hz/wishlist/ls/DANA",
    })
    assert r.json() == {"message": "Unable to create new profile. Profile already created."}


def test_create_profile_and_open_teacher_page(fresh_db):
    """The profile half of the journey, for a user whose createCount is 0."""
    from app import database
    from app import models

    db = database.SessionLocal()
    db.add(models.RegisteredUsers(email="erin@example.com", phone_number="5553334444",
                               password=db.query(models.RegisteredUsers.password).first()[0],
                               role="teacher", createCount=0))
    db.commit()
    db.close()

    erin = helpers.client()
    r = login(erin, "erin@example.com")
    assert r.json() == {"message": "Login successful as teacher", "createCount": 0, "role": "teacher"}

    r = erin.post("/profile/create_teacher_profile/", data={
        "name": "Erin Evans", "state": "Texas", "county": "Bexar",
        "district": "San Antonio ISD", "school": "Alamo Elementary",
        "aboutMe": "PE teacher.", "wishlist": "https://www.amazon.com/hz/wishlist/ls/ERIN",
    })
    assert r.json() == {"message": "Teacher created successfully", "role": "teacher"}

    r = erin.post("/profile/create_teacher_profile/", data={
        "name": "Erin Again", "state": "Texas", "county": "Bexar",
        "district": "San Antonio ISD", "school": "Alamo Elementary",
        "aboutMe": "x", "wishlist": "https://www.amazon.com/hz/wishlist/ls/ERIN",
    })
    assert r.json() == {"message": "Unable to create new profile. Profile already created."}

    r = erin.get("/profile/myinfo/")
    assert r.json() == {"state": "Texas", "county": "Bexar", "district": "San Antonio ISD",
                        "school": "Alamo Elementary", "teacher": "Erin Evans"}

    db = database.SessionLocal()
    url_id = db.query(models.TeacherList.url_id).filter(models.TeacherList.name == "Erin Evans").scalar()
    db.close()
    assert re.fullmatch(r"erin\d{1,4}", url_id)

    visitor = helpers.client()
    r = visitor.get(f"/teacher/{url_id}")
    assert r.status_code == 307
    assert r.headers["location"] == "/pages/teacher.html"
    r = visitor.get("/api/get_teacher_info/")
    assert r.json()["name"] == "Erin Evans"
    assert r.json()["wishlist_url"] == "https://www.amazon.com/hz/wishlist/ls/ERIN&tag=h0mer00mher0-20"

    r = erin.get("/api/check_access_teacher/")
    assert r.json() == {"status": "success", "message": "Access granted"}


def test_forgot_and_reset_password(fresh_db, monkeypatch):
    from app.routers import auth

    outbox = fresh_db
    visitor = helpers.client()
    r = visitor.post("/profile/forgot_password/", data={"email": "bob@example.com"})
    assert r.json() == {"message": "If an account exists, a reset link will be sent to your email."}
    token = re.search(r"token=([\w-]+)", outbox.sent[-1]["content"]["plainText"]).group(1)

    # Unknown address: same answer, no email.
    monkeypatch.setattr(auth.time, "sleep", lambda s: None)
    sent_before = len(outbox.sent)
    r = visitor.post("/profile/forgot_password/", data={"email": "nobody@example.com"})
    assert r.json() == {"message": "If an account exists, a reset link will be sent to your email."}
    assert len(outbox.sent) == sent_before

    r = visitor.post("/profile/reset_password/", data={
        "token": token, "new_password": "New-Passw0rd!", "confirm_password": "Mismatch!"})
    assert r.status_code == 400

    r = visitor.post("/profile/reset_password/", data={
        "token": token, "new_password": "New-Passw0rd!", "confirm_password": "New-Passw0rd!"})
    assert r.json() == {"message": "Password reset successfully. You can now log in."}

    # The token works once.
    r = visitor.post("/profile/reset_password/", data={
        "token": token, "new_password": "Other-Passw0rd!", "confirm_password": "Other-Passw0rd!"})
    assert r.status_code == 400

    bob = helpers.client()
    assert login(bob, "bob@example.com").json() == {"message": "Invalid login credentials."}
    assert login(bob, "bob@example.com", "New-Passw0rd!").json()["message"] == "Login successful as teacher"


def test_forum_post_comment_vote_edit_delete(fresh_db):
    alice, bob, admin = helpers.client(), helpers.client(), helpers.client()
    login(alice, "alice@example.com")
    login(bob, "bob@example.com")
    login(admin, "admin@example.com")

    # Logged out can't post.
    assert helpers.client().post("/forum/create_post", data={"title": "x", "content": "y"}).status_code == 401

    r = alice.post("/forum/create_post", data={
        "title": "Field trip <script>x</script>ideas", "content": "<p>Where do you <b>go</b>?</p>"})
    assert r.status_code == 200
    post = r.json()
    assert post["title"] == "Field trip xideas"  # tags outside the allow list are stripped
    assert post["content"] == "<p>Where do you <b>go</b>?</p>"
    assert (post["upvote_count"], post["comment_count"]) == (0, 0)
    post_id = post["id"]

    r = bob.post(f"/forum/posts/{post_id}/comment", data={"content": "The science museum."})
    assert r.status_code == 200
    comment_id = r.json()["id"]
    r = alice.post(f"/forum/posts/{post_id}/comment",
                   data={"content": "Good one!", "parent_comment_id": str(comment_id)})
    assert r.json()["parent_comment_id"] == comment_id
    assert helpers.client().get(f"/forum/get_post?post_id={post_id}").json()["comment_count"] == 2

    # Vote: up, same again retracts, then down.
    assert bob.post(f"/forum/posts/{post_id}/vote", json={"vote_type": 1}).json()["upvote_count"] == 1
    assert bob.post(f"/forum/posts/{post_id}/vote", json={"vote_type": 1}).json()["upvote_count"] == 0
    assert bob.post(f"/forum/posts/{post_id}/vote", json={"vote_type": -1}).json()["upvote_count"] == -1
    assert alice.post(f"/forum/posts/{post_id}/vote", json={"vote_type": 1}).json()["upvote_count"] == 0
    assert bob.post(f"/forum/posts/{post_id}/vote", json={"vote_type": 1}).json()["upvote_count"] == 2
    assert bob.post(f"/forum/posts/{post_id}/vote", json={"vote_type": 5}).status_code == 400

    # Edit: only the author. Others get 500, not 403, because the 403 is
    # raised inside a broad except (see BE3-1).
    r = bob.patch(f"/forum/post/{post_id}/update", json={"title": "Hacked", "content": "x"})
    assert r.status_code == 500
    r = alice.patch(f"/forum/post/{post_id}/update", json={"title": "Field trips", "content": "<p>Updated</p>"})
    assert r.status_code == 200
    assert (r.json()["title"], r.json()["content"]) == ("Field trips", "<p>Updated</p>")

    r = alice.patch(f"/forum/comment/{comment_id}/update", data={"content": "Not mine"})
    assert r.status_code == 500
    r = bob.patch(f"/forum/comment/{comment_id}/update", data={"content": "The art museum."})
    assert r.json()["content"] == "The art museum."

    # Delete: admin only, for comments and posts.
    assert bob.delete(f"/forum/comment/{comment_id}/delete").status_code == 403
    assert alice.delete(f"/forum/post/{post_id}/delete").status_code == 403

    reply_id = comment_id + 1
    r = admin.delete(f"/forum/comment/{reply_id}/delete")
    assert r.json() == {"detail": f"Comment ID {reply_id} successfully deleted."}
    assert helpers.client().get(f"/forum/get_post?post_id={post_id}").json()["comment_count"] == 1


def test_delete_post_with_comments(fresh_db):
    """Deleting a post that still has comments or votes.

    The handler's comment says the database cascades, but the models
    declare no ON DELETE CASCADE, so the delete fails. This records
    today's behaviour; BE2-8 decides what it should do.
    """
    admin = helpers.client()
    login(admin, "admin@example.com")
    with pytest.raises(Exception, match="REFERENCE constraint"):
        admin.delete("/forum/post/1/delete")
