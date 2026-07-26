from backend.jobs.legacy import LegacyJobService


class RecordingEmailProvider:
    def __init__(self):
        self.messages = []

    def send(self, recipient, subject, html_message, plain_message):
        self.messages.append(
            (recipient, subject, html_message, plain_message)
        )
        return True

    def send_attachment(self, *args, **kwargs):
        return True


class NoopRecaptchaProvider:
    def verify(self, _response):
        return True


class NoopXProvider:
    def publish(self, _text):
        return None


class FailingEmailProvider(RecordingEmailProvider):
    def send(self, *args, **kwargs):
        return False


def make_service():
    email_provider = RecordingEmailProvider()
    service = LegacyJobService(
        session_factory=lambda: None,
        database_url="sqlite:///:memory:",
        email_provider=email_provider,
        recaptcha_provider=NoopRecaptchaProvider(),
        x_provider=NoopXProvider(),
        render_email_template=lambda _template, data: (
            f"HTML:{data['recipient_name']}:{data['message_body']}"
        ),
    )
    return service, email_provider


def test_registration_notification_preserves_body_and_subject():
    service, email_provider = make_service()

    service.send_registration_email("new@example.test")

    recipient, subject, html, plain = email_provider.messages[0]
    assert recipient == "new@example.test"
    assert subject == "Registration successful"
    assert "Thank you for registering with us!" in html
    assert plain.count("Thank you for registering with us!") == 1
    assert plain.startswith("Dear new@example.test,\n\n")


def test_registration_notification_reports_provider_failure():
    service = LegacyJobService(
        session_factory=lambda: None,
        database_url="sqlite:///:memory:",
        email_provider=FailingEmailProvider(),
        recaptcha_provider=NoopRecaptchaProvider(),
        x_provider=NoopXProvider(),
        render_email_template=lambda _template, data: data["message_body"],
    )

    assert service.send_registration_email("new@example.test") is False


def test_profile_reminder_notification_preserves_single_contact_sentence():
    service, email_provider = make_service()

    service.send_profile_reminder_email("teacher@example.test")

    _, subject, _, plain = email_provider.messages[0]
    assert subject == "Reminder: Complete Your Homeroom Heroes Profile!"
    assert plain.count("If you have any questions or need assistance") == 1


def test_extracted_job_entrypoints_preserve_delegation():
    service, _ = make_service()
    calls = []
    service.send_profile_creation_reminders = lambda: calls.append("profile")
    service.send_validation_reminder_emails = lambda: calls.append("validation")

    service.tuesday_job()
    service.thursday_job()

    assert calls == ["profile", "validation"]
