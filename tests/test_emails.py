"""BE1-5: saved subject, recipients, HTML and plain text for all 8 emails.

BE5-1 merges the 8 email functions into one sender; the wording must
survive. Each test triggers one email with the Azure client replaced by
a fake (tests/helpers.py) and compares with tests/golden/emails/:
  <name>.json  sender, recipients, subject and plain text
  <name>.html  HTML body

After an intended wording change, regenerate with:
    UPDATE_GOLDEN=1 TEST_DATABASE=1 pytest tests/test_emails.py
and review the diff under tests/golden/emails/.
"""
import json
from pathlib import Path

from tests import helpers
from tests.helpers import outbox, requires_db  # noqa: F401  (fixture)
from tests.testenv import update_golden

GOLDEN_DIR = Path(__file__).parent / "golden" / "emails"
FIXED_TOKEN = "TEST-RESET-TOKEN"


def check_golden(name: str, messages: list[dict]) -> None:
    assert messages, f"{name}: no email was sent"
    meta = [
        {
            "sender": m["senderAddress"],
            "to": [r["address"] for r in m["recipients"]["to"]],
            "subject": m["content"]["subject"],
            "plain_text": m["content"]["plainText"],
        }
        for m in messages
    ]
    # Every message of one kind uses the same HTML template; keep the first.
    html = messages[0]["content"]["html"]

    meta_path = GOLDEN_DIR / f"{name}.json"
    html_path = GOLDEN_DIR / f"{name}.html"
    if update_golden():
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        html_path.write_text(html, encoding="utf-8")
    assert meta == json.loads(meta_path.read_text(encoding="utf-8")), f"{name}: subject, recipients or text changed"
    assert html == html_path.read_text(encoding="utf-8"), f"{name}: HTML changed"


def test_registration_email(outbox):
    from app.services import emailer

    emailer.send_registration_email("new.teacher@example.com")
    check_golden("registration", outbox.sent)


def test_validation_email(outbox):
    from app.services import emailer

    emailer.send_validation_email("new.teacher@example.com")
    check_golden("validation", outbox.sent)


def test_teacher_of_the_day_email(outbox):
    from app.services import emailer

    emailer.send_teacher_of_the_day_email("alice@example.com", "Alice Adams", "alice1234")
    check_golden("teacher_of_the_day", outbox.sent)


def test_contact_us_email(outbox):
    c = helpers.client()
    response = c.post("/api/contact_us/", data={
        "name": "Jo <b>Parent</b>", "email": "jo@example.com",
        "subject": "Question", "message": "How do I <i>donate</i>?",
        "recaptcha_response": "ok",
    })
    assert response.status_code == 200
    check_golden("contact_us", outbox.sent)


@requires_db
def test_pending_validation_email(outbox):
    """Wednesday job: tells teachers in a district who is waiting."""
    from app.services import jobs

    jobs.wednesday_job()
    outbox.sent.sort(key=lambda m: m["recipients"]["to"][0]["address"])
    check_golden("pending_validation", outbox.sent)


@requires_db
def test_profile_reminder_email(outbox):
    """Tuesday job: validated users who have not made a profile."""
    from app.services import jobs

    jobs.tuesday_job()
    check_golden("profile_reminder", outbox.sent)


@requires_db
def test_validation_reminder_email(outbox):
    """Thursday job: registered users still waiting for validation."""
    from app.services import jobs

    jobs.thursday_job()
    check_golden("validation_reminder", outbox.sent)


@requires_db
def test_password_reset_email(outbox, monkeypatch):
    from app import database
    from app import models
    from app.routers import auth

    monkeypatch.setattr(auth.secrets, "token_urlsafe", lambda n: FIXED_TOKEN)
    c = helpers.client()
    response = c.post("/profile/forgot_password/", data={"email": "bob@example.com"})
    assert response.status_code == 200
    try:
        check_golden("password_reset", outbox.sent)
    finally:
        # Leave the seeded database as it was for other tests.
        db = database.SessionLocal()
        db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token == FIXED_TOKEN).delete()
        db.commit()
        db.close()
