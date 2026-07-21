"""Compatibility notifications and scheduled jobs preserved from the legacy app."""

import os
from datetime import date

from fastapi import Request
from passlib.hash import sha256_crypt
from sqlalchemy import String, cast, delete, func, select, update

from backend.db.models import NewUsers, RegisteredUsers, Spotlight, TeacherList


class LegacyJobService:
    """Behavior-preserving home for the legacy notification and job functions."""

    def __init__(
        self,
        *,
        session_factory,
        database_url,
        email_provider,
        recaptcha_provider,
        x_provider,
        render_email_template,
    ):
        self.session_factory = session_factory
        self.database_url = database_url
        self.email_provider = email_provider
        self.recaptcha_provider = recaptcha_provider
        self.x_provider = x_provider
        self.render_email_template = render_email_template

    def send_email(self, recipient_email, subject, html_message, plain_message):
        return self.email_provider.send(
            recipient_email, subject, html_message, plain_message
        )

    def send_attachment(self, recipient_email, subject, message, attachment_path):
        return self.email_provider.send_attachment(
            recipient_email, subject, message, attachment_path
        )

    def send_registration_email(self, recipient_email):
        template_data = {
            "recipient_name": recipient_email,
            "message_body": (
                "Thank you for registering with us! Once you are validated by a "
                "fellow teacher in your district or one of us here at Homeroom Heroes, "
                "you will be able to create your profile and start receiving support."
            ),
        }
        html_message = self.render_email_template(
            "static/email_template.html", template_data
        )
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "Best regards,\nHomeroom Heroes Team\n"
            "homeroom.heroes.contact@gmail.com\n"
            "homeroom.heroes.contact@gmail.com"
        )
        return self.send_email(
            recipient_email,
            "Registration successful",
            html_message,
            plain_message,
        )

    def send_validation_email(self, recipient_email):
        template_data = {
            "recipient_name": recipient_email,
            "message_body": (
                "We are pleased to inform you that your registration with us has been "
                "successfully validated! You may now log in and create your profile "
                "to start receiving support."
            ),
        }
        html_message = self.render_email_template(
            "static/email_template.html", template_data
        )
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
            "Best regards,\nHomeroom Heroes Team\n"
            "homeroom.heroes.contact@gmail.com"
        )
        return self.send_email(
            recipient_email,
            "Validation Notification",
            html_message,
            plain_message,
        )

    def update_temp_password(self, db, email, new_password):
        try:
            hashed_password = sha256_crypt.hash(new_password)
            query = (
                update(RegisteredUsers)
                .where(
                    cast(RegisteredUsers.email, String) == cast(email, String)
                )
                .values(password=hashed_password)
            )
            db.execute(query)
            db.commit()
        except Exception as exc:
            print(f"Error updating password: {exc}")
            raise

    def fetch_random_teacher(self):
        db = self.session_factory()
        try:
            ordering = func.random() if self.database_url.startswith("sqlite") else func.newid()
            query = select(TeacherList).order_by(ordering).limit(1)
            return db.execute(query).scalar_one_or_none()
        except Exception as exc:
            print(f"Error fetching random teacher: {exc}")
            return None
        finally:
            db.close()

    def store_spotlight(self, teacher_info: dict, token: str):
        db = self.session_factory()
        try:
            delete_query = delete(Spotlight).where(
                cast(Spotlight.token, String) == cast(token, String)
            )
            db.execute(delete_query)
            if token == "teacher":
                spotlight_entry = Spotlight(
                    state=teacher_info["state"],
                    county=teacher_info["county"],
                    district=teacher_info["district"],
                    school=teacher_info["school"],
                    name=teacher_info["name"],
                    token=token,
                    image_data=teacher_info["image_data"],
                )
            elif token == "district":
                spotlight_entry = Spotlight(
                    state=teacher_info["state"],
                    county=teacher_info["county"],
                    district=teacher_info["district"],
                    token=token,
                )
            elif token == "county":
                spotlight_entry = Spotlight(
                    state=teacher_info["state"],
                    county=teacher_info["county"],
                    token=token,
                )
            db.add(spotlight_entry)
            db.commit()
        except Exception as exc:
            db.rollback()
            raise exc
        finally:
            db.close()

    def send_teacher_of_the_day_email(self, recipient_email, recipient_name, url_id):
        template_data = {
            "recipient_name": recipient_name,
            "message_body": (
                "Congratulations! You've been chosen as today's 'Teacher of the Day' at Homeroom Heroes! "
                "Your profile is now featured on our homepage, giving you extra visibility. "
                "Remember to share your unique page with your community. "
                f"www.HelpTeachers.net/teacher/{url_id}"
            ),
        }
        html_message = self.render_email_template(
            "static/email_template.html", template_data
        )
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "Best regards,\nHomeroom Heroes Team\n"
            "homeroom.heroes.contact@gmail.com"
        )
        self.send_email(
            recipient_email,
            "🎉 You're Today's Homeroom Hero!",
            html_message,
            plain_message,
        )

    def daily_job(self):
        db = self.session_factory()
        try:
            random_teacher = self.fetch_random_teacher()
            if random_teacher:
                teacher_info = {
                    "name": random_teacher.name,
                    "state": random_teacher.state,
                    "county": random_teacher.county,
                    "district": random_teacher.district,
                    "school": random_teacher.school,
                    "image_data": random_teacher.image_data,
                    "url_id": random_teacher.url_id,
                }
                self.store_spotlight(teacher_info, "teacher")
                email_query = select(RegisteredUsers.email).where(
                    RegisteredUsers.id == random_teacher.regUserID
                )
                teacher_email = db.execute(email_query).scalar_one_or_none()
                teacher_url = f"www.HelpTeachers.net/teacher/{random_teacher.url_id}"
                tweet_message = (
                    f"Today's #TeacherOfTheDay is {random_teacher.name}! "
                    f"You can support their classroom and mission here: {teacher_url}"
                    f"#HomeroomHeroes #Education"
                )
                self.post_tweet_x(tweet_message)
                if teacher_email:
                    self.send_teacher_of_the_day_email(
                        recipient_email=teacher_email,
                        recipient_name=teacher_info["name"],
                        url_id=teacher_info["url_id"],
                    )
                else:
                    print(
                        f"No email found for teacher: {random_teacher.name}. "
                        "Spotlight stored, but no email sent."
                    )
            else:
                print("No random teacher found.")
        except Exception as exc:
            print(f"Error in daily_job: {exc}")
        finally:
            db.close()

    def monday_job(self):
        random_teacher = self.fetch_random_teacher()
        if random_teacher:
            self.store_spotlight(
                {
                    "state": random_teacher[0].state,
                    "county": random_teacher[0].county,
                    "district": random_teacher[0].district,
                },
                "district",
            )
        else:
            print("No random teacher found.")

    def first_of_month_job(self):
        if date.today().day == 1:
            random_teacher = self.fetch_random_teacher()
            if random_teacher:
                self.store_spotlight(
                    {
                        "state": random_teacher[0].state,
                        "county": random_teacher[0].county,
                    },
                    "county",
                )
            else:
                print("No random teacher found.")
        else:
            print("Not the first.")

    def wednesday_job(self):
        db = self.session_factory()
        try:
            pending_groups = (
                db.query(
                    cast(NewUsers.state, String),
                    cast(NewUsers.county, String),
                    cast(NewUsers.district, String),
                )
                .group_by(
                    cast(NewUsers.state, String),
                    cast(NewUsers.county, String),
                    cast(NewUsers.district, String),
                )
                .all()
            )
            for state, county, district in pending_groups:
                recipients = (
                    db.query(RegisteredUsers.email)
                    .join(TeacherList, TeacherList.regUserID == RegisteredUsers.id)
                    .filter(
                        cast(TeacherList.state, String) == state,
                        cast(TeacherList.county, String) == county,
                        cast(TeacherList.district, String) == district,
                    )
                    .all()
                )
                recipient_emails = [recipient.email for recipient in recipients]
                if not recipient_emails:
                    print(f"No validated teachers found for {district}. Skipping.")
                    continue
                pending_teachers = (
                    db.query(NewUsers)
                    .filter(
                        cast(NewUsers.state, String) == state,
                        cast(NewUsers.county, String) == county,
                        cast(NewUsers.district, String) == district,
                    )
                    .all()
                )
                if not pending_teachers:
                    continue
                teacher_lines = [
                    f"- {teacher.name} ({teacher.school})"
                    for teacher in pending_teachers
                ]
                email_body = (
                    f"Hello,\n\nThe following teachers in {district} are waiting to be validated:\n\n"
                    + "\n".join(teacher_lines)
                    + "\n\nPlease log in to validate them.\n\nThank you!"
                )
                try:
                    for email in recipient_emails:
                        template_data = {
                            "recipient_name": email,
                            "message_body": email_body,
                        }
                        html_message = self.render_email_template(
                            "static/email_template.html", template_data
                        )
                        plain_message = (
                            f"Dear {email},\n\n{email_body}\n\n"
                            "Best regards,\nHomeroom Heroes Team\n"
                            "homeroom.heroes.contact@gmail.com"
                        )
                        self.send_email(
                            email,
                            f"Pending Teachers in {district} Need Validation",
                            html_message,
                            plain_message,
                        )
                    print(
                        f"Sent validation email to {district} "
                        f"({len(recipient_emails)} recipients)."
                    )
                except Exception as exc:
                    print(f"Failed to send email for {district}: {exc}")
                    continue
        except Exception as exc:
            print(f"Error in wednesday_validation_job: {exc}")
        finally:
            db.close()

    def send_profile_creation_reminders(self):
        db = self.session_factory()
        try:
            users = db.execute(
                select(RegisteredUsers).where(RegisteredUsers.createCount == 0)
            ).scalars().all()
            if users:
                print(f"Found {len(users)} users who need a profile reminder.")
                for user in users:
                    self.send_profile_reminder_email(user.email)
                print("Successfully sent all profile creation reminder emails.")
            else:
                print("No users found with a createCount of 0.")
        except Exception as exc:
            print(f"An error occurred while sending profile reminders: {str(exc)}")
        finally:
            db.close()

    def send_profile_reminder_email(self, recipient_email):
        template_data = {
            "recipient_name": recipient_email,
            "message_body": (
                "You're almost there! Your registration with us has been "
                "successfully validated, but you haven't created your profile yet. "
                "Please log in and complete your profile to start receiving support from our community.\n"
                "www.HelpTeachers.net/login"
            ),
        }
        html_message = self.render_email_template(
            "static/email_template.html", template_data
        )
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
            "Best regards,\nHomeroom Heroes Team\n"
            "homeroom.heroes.contact@gmail.com"
        )
        self.send_email(
            recipient_email,
            "Reminder: Complete Your Homeroom Heroes Profile!",
            html_message,
            plain_message,
        )

    def tuesday_job(self):
        self.send_profile_creation_reminders()
        print("Tuesday job to send profile creation reminders has completed.")

    def send_validation_reminder_emails(self):
        db = self.session_factory()
        try:
            users = db.execute(select(NewUsers)).scalars().all()
            if users:
                print(f"Found {len(users)} new users who need a validation reminder.")
                for user in users:
                    self.send_validation_reminder_email(user.email)
                print("Successfully sent all new user validation reminder emails.")
            else:
                print("No new users found who need a validation reminder.")
        except Exception as exc:
            print(f"An error occurred while sending new user reminders: {str(exc)}")
        finally:
            db.close()

    def send_validation_reminder_email(self, recipient_email):
        template_data = {
            "recipient_name": recipient_email,
            "message_body": (
                "Thanks for signing up! We noticed you haven't been validated yet. "
                "Please reach back out to us at homeroom.heroes.contact@gmail.com to complete your validation process."
            ),
        }
        html_message = self.render_email_template(
            "static/email_template.html", template_data
        )
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "Best regards,\nHomeroom Heroes Team\n"
            "homeroom.heroes.contact@gmail.com"
        )
        self.send_email(
            recipient_email,
            "Reminder: Complete Your Homeroom Heroes Validation!",
            html_message,
            plain_message,
        )

    def thursday_job(self):
        self.send_validation_reminder_emails()
        print("Thursday job to send new user validation reminders has completed.")

    def post_tweet_x(self, tweet_text):
        return self.x_provider.publish(tweet_text)

    def verify_recaptcha(self, recaptcha_response):
        return self.recaptcha_provider.verify(recaptcha_response)

    def verify_cronjob_request(self, request: Request):
        secret = request.headers.get("x-secret-key")
        if not secret or secret != os.getenv("INTERNAL_JOB_SECRET"):
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Forbidden")

    @staticmethod
    def model_to_dict(model):
        data = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            data[column.name] = value.isoformat() if hasattr(value, "isoformat") else value
        return data
