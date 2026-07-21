"""External-provider adapters with bounded calls and safe failure logging."""

import base64
import logging
import mimetypes
import os
from pathlib import Path
from typing import Protocol

import requests

try:
    from azure.communication.email import EmailClient
except ImportError:  # pragma: no cover - optional production dependency
    EmailClient = None

try:
    from tweepy import Client
except ImportError:  # pragma: no cover - optional production dependency
    Client = None


logger = logging.getLogger("backend.integrations")


class EmailProvider(Protocol):
    def send(self, recipient_email: str, subject: str, html: str, plain: str): ...

    def send_attachment(
        self, recipient_email: str, subject: str, message: str, attachment_path: str
    ): ...


class AzureEmailProvider:
    def __init__(self, *, app_env: str, timeout_seconds: float = 10.0, client_factory=None):
        self.app_env = app_env
        self.timeout_seconds = timeout_seconds
        self.client_factory = client_factory or EmailClient

    def _client(self):
        if self.client_factory is None:
            return None
        connection_string = os.getenv("AZURE_EMAIL_CONNECTION_STRING")
        if not connection_string:
            return None
        return self.client_factory.from_connection_string(connection_string)

    def send(self, recipient_email: str, subject: str, html: str, plain: str):
        if self.app_env in {"test", "dev", "development", "local"}:
            return True
        client = self._client()
        if client is None:
            logger.warning("email_provider_unconfigured", extra={"provider": "azure"})
            return False
        try:
            poller = client.begin_send(
                {
                    "senderAddress": os.getenv("AZURE_EMAIL_SENDER"),
                    "recipients": {"to": [{"address": recipient_email}]},
                    "content": {"subject": subject, "html": html, "plainText": plain},
                }
            )
            poller.result(timeout=self.timeout_seconds)
            return True
        except Exception:
            logger.exception("email_provider_failed", extra={"provider": "azure"})
            return False

    def send_attachment(self, recipient_email, subject, message, attachment_path):
        if self.app_env in {"test", "dev", "development", "local"}:
            return True
        client = self._client()
        if client is None:
            logger.warning("email_provider_unconfigured", extra={"provider": "azure"})
            return False
        try:
            path = Path(attachment_path)
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            encoded_content = base64.b64encode(path.read_bytes()).decode("ascii")
            poller = client.begin_send(
                {
                    "senderAddress": os.getenv("AZURE_EMAIL_SENDER"),
                    "recipients": {"to": [{"address": recipient_email}]},
                    "content": {"subject": subject, "plainText": message, "html": f"<p>{message}</p>"},
                    "attachments": [{"name": path.name, "contentType": content_type, "contentInBase64": encoded_content}],
                }
            )
            return poller.result(timeout=self.timeout_seconds)
        except Exception:
            logger.exception("email_attachment_provider_failed", extra={"provider": "azure"})
            return False


class RecaptchaProvider:
    def __init__(self, *, app_env: str, secret_key: str | None, expected_test_token: str, timeout_seconds: float = 5.0, session=None):
        self.app_env = app_env
        self.secret_key = secret_key
        self.expected_test_token = expected_test_token
        self.timeout_seconds = timeout_seconds
        self.session = session or requests

    def verify(self, response_token: str):
        if self.app_env in {"test", "dev", "development", "local"}:
            return response_token == self.expected_test_token
        if not self.secret_key or not response_token:
            return False
        try:
            response = self.session.post(
                "https://www.google.com/recaptcha/api/siteverify",
                params={"secret": self.secret_key, "response": response_token},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return bool(response.json().get("success", False))
        except Exception:
            logger.exception("recaptcha_provider_failed", extra={"provider": "google"})
            return False


class XProvider:
    def __init__(self, *, client_factory=None):
        self.client_factory = client_factory or Client

    def publish(self, text: str):
        credentials = [
            os.getenv("X_API_KEY"),
            os.getenv("X_API_SECRET"),
            os.getenv("X_ACCESS_TOKEN"),
            os.getenv("X_ACCESS_TOKEN_SECRET"),
        ]
        if not all(credentials) or self.client_factory is None:
            logger.info("x_provider_skipped", extra={"reason": "unconfigured"})
            return None
        try:
            client = self.client_factory(
                consumer_key=credentials[0],
                consumer_secret=credentials[1],
                access_token=credentials[2],
                access_token_secret=credentials[3],
            )
            return client.create_tweet(text=text)
        except Exception:
            logger.exception("x_provider_failed", extra={"provider": "x"})
            return None


def render_email_template(template_path: str, data: dict) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    for key, value in data.items():
        template = template.replace(f"{{{{ {key} }}}}", str(value))
    return template
