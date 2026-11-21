"""Helpers for tests that call the app.

Sessions are signed cookies (Starlette SessionMiddleware). Tests build a
logged-in session directly instead of calling /profile/login/, which is
rate limited to 5 a minute.
"""
import base64
import json
import os

import itsdangerous
import pytest
from fastapi.testclient import TestClient

from tests import testenv

requires_db = pytest.mark.skipif(
    not testenv.use_database(),
    reason="needs the test database: run scripts/test_db.sh, then TEST_DATABASE=1 pytest",
)

# Seeded users (see tests/seed.py). Ids follow insert order.
ADMIN = {"user_id": 1, "user_email": "admin@example.com", "user_role": "admin"}
ALICE = {"user_id": 2, "user_email": "alice@example.com", "user_role": "teacher"}
BOB = {"user_id": 3, "user_email": "bob@example.com", "user_role": "teacher"}
CAROL = {"user_id": 4, "user_email": "carol@example.com", "user_role": "teacher"}

# Session keys the teacher pages use to know which teacher is shown.
ALICE_PAGE = {"state": "Illinois", "county": "Sangamon",
              "district": "Springfield District", "school": "Lincoln Elementary",
              "teacher": "Alice Adams"}
BOB_PAGE = {**ALICE_PAGE, "teacher": "Bob Brown"}


def _signer() -> itsdangerous.TimestampSigner:
    return itsdangerous.TimestampSigner(os.environ["SECRET_KEY"])


def encode_session(data: dict) -> str:
    payload = base64.b64encode(json.dumps(data).encode("utf-8"))
    return _signer().sign(payload).decode("utf-8")


def decode_session(cookie: str | None) -> dict:
    if not cookie:
        return {}
    payload = _signer().unsign(cookie)
    return json.loads(base64.b64decode(payload))


def client(session: dict | None = None) -> TestClient:
    from app.main import app as fastapi_app

    c = TestClient(fastapi_app, base_url="https://testserver", follow_redirects=False)
    if session:
        c.cookies.set("session", encode_session(session), domain="testserver.local")
    return c


def session_of(c: TestClient) -> dict:
    return decode_session(c.cookies.get("session"))


class FakeEmailClient:
    """Stands in for azure EmailClient and records every message sent."""

    def __init__(self):
        self.sent: list[dict] = []

    def begin_send(self, message: dict):
        self.sent.append(message)
        return _DonePoller()


class _DonePoller:
    def result(self):
        return {"status": "Succeeded", "id": "fake"}


@pytest.fixture
def outbox(monkeypatch) -> FakeEmailClient:
    """Replace the Azure email client; the fixture's .sent lists messages."""
    import sys

    from azure.communication.email import EmailClient

    import app.main  # noqa: F401  (imports every router)

    fake = FakeEmailClient()
    monkeypatch.setattr(EmailClient, "from_connection_string",
                        staticmethod(lambda conn: fake))
    # Routers import verify_recaptcha by name, so patch it where it is used.
    for name, module in list(sys.modules.items()):
        if name.startswith("app.") and hasattr(module, "verify_recaptcha"):
            monkeypatch.setattr(module, "verify_recaptcha", lambda response: True)
    return fake


db_dirty = False


def reseed() -> None:
    import gc

    from app.database import engine
    from tests import seed

    # Many handlers open a session and never close it. Collect those now,
    # while the database still exists, so their connections are returned
    # cleanly instead of failing later in an unrelated test. BE2-4 (get_db)
    # removes the need for this.
    gc.collect()
    engine.dispose()
    seed.recreate_database()
    seed.seed()
    engine.dispose()


@pytest.fixture
def fresh_db(outbox):
    """Reseed the test database before a test that writes to it.

    Also switches off rate limits (login, register, posting and commenting
    allow 5 a minute) and fakes email and reCAPTCHA through `outbox`.
    Yields the outbox.
    """
    from app.limiter import limiter

    reseed()
    global db_dirty
    db_dirty = True
    limiter.enabled = False
    try:
        yield outbox
    finally:
        limiter.enabled = True
