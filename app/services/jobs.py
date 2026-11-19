"""Scheduled jobs (daily, Tuesday, Wednesday, Thursday) and the helpers they run."""
import datetime
from sqlalchemy import String
from sqlalchemy.sql import select, cast, update

from app.database import SessionLocal
from app.models import NewUsers, RegisteredUsers, TeacherList
from app.services.emailer import (
    render_email_template,
    send_email,
    send_teacher_of_the_day_email,
    send_profile_reminder_email,
    send_validation_reminder_email,
)
from app.services.teachers import fetch_teacher_for_tod

def daily_job():
    db = SessionLocal()
    try:
        # Picks a teacher who hasn't been Teacher of the Day in the last 90 days
        chosen_teacher = fetch_teacher_for_tod()

        if chosen_teacher:
            teacher_info = {
                "name": chosen_teacher.name,
                "state": chosen_teacher.state,
                "county": chosen_teacher.county,
                "district": chosen_teacher.district,
                "school": chosen_teacher.school,
                "image_data": chosen_teacher.image_data,
                "url_id": chosen_teacher.url_id
            }

            # Stamp last_TOD on the chosen teacher so they're excluded from
            # selection for the next 90 days.
            update_query = (
                update(TeacherList)
                .where(TeacherList.id == chosen_teacher.id)
                .values(last_TOD=datetime.datetime.utcnow())
            )
            db.execute(update_query)
            db.commit()

            # Now, attempt to fetch the email and send the notification
            email_query = select(RegisteredUsers.email).where(RegisteredUsers.id == chosen_teacher.regUserID)
            teacher_email = db.execute(email_query).scalar_one_or_none()

            if teacher_email:
                # Send the email notification
                send_teacher_of_the_day_email(
                    recipient_email=teacher_email,
                    recipient_name=teacher_info["name"],
                    url_id=teacher_info["url_id"]
                )
            else:
                print(f"No email found for teacher: {chosen_teacher.name}. last_TOD updated, but no email sent.")
        else:
            print("No eligible teacher found.")
    except Exception as e:
        db.rollback()
        print(f"Error in daily_job: {e}")
    finally:
        db.close()

def wednesday_job():
    db = SessionLocal()
    try:
        # 1. Find all districts with pending teachers
        pending_groups = (
            db.query(
                cast(NewUsers.state, String),
                cast(NewUsers.county, String),
                cast(NewUsers.district, String)
            )
            .group_by(
                cast(NewUsers.state, String),
                cast(NewUsers.county, String),
                cast(NewUsers.district, String)
            )
            .all()
        )
        for state, county, district in pending_groups:
            # 2. Find validated teachers in this district (recipients)
            recipients = (
                db.query(RegisteredUsers.email)
                .join(TeacherList, TeacherList.regUserID == RegisteredUsers.id)
                .filter(
                    cast(TeacherList.state, String) == state,
                    cast(TeacherList.county, String) == county,
                    cast(TeacherList.district, String) == district
                )
                .all()
            )
            recipient_emails = [r.email for r in recipients]
            if not recipient_emails:
                print(f"No validated teachers found for {district}. Skipping.")
                continue
            # 3. Get pending teachers in this district
            pending_teachers = (
                db.query(NewUsers)
                .filter(
                    cast(NewUsers.state, String) == state,
                    cast(NewUsers.county, String) == county,
                    cast(NewUsers.district, String) == district
                )
                .all()
            )
            if not pending_teachers:
                continue
            # 4. Build email body
            teacher_lines = [
                f"- {t.name} ({t.school})"
                for t in pending_teachers
            ]
            email_body = (
                f"Hello,\n\n"
                f"The following teachers in {district} are waiting to be validated:\n\n"
                + "\n".join(teacher_lines)
                + "\n\nPlease log in to validate them.\n\n"
                "Thank you!"
            )
            # 5. Send the email
            try:
                for email in recipient_emails:
                    template_data = {
                        'recipient_name': email,
                        'message_body': email_body
                    }
                    html_message = render_email_template('static/email_template.html', template_data)
                    plain_message = (
                        f"Dear {email},\n\n"
                        f"{email_body}\n\n"
                        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
                    )
                    send_email(
                        email,
                        f"Pending Teachers in {district} Need Validation",
                        html_message,
                        plain_message
                    )
                print(f"Sent validation email to {district} ({len(recipient_emails)} recipients).")
            except Exception as e:
                print(f"Failed to send email for {district}: {e}")
                continue
    except Exception as e:
        print(f"Error in wednesday_validation_job: {e}")
    finally:
        db.close()

def send_profile_creation_reminders():
    """
    Checks the RegisteredUsers table and sends a profile creation reminder
    email to all users who have not yet created a profile.
    """
    db = SessionLocal()
    try:
        # Query for users with createCount equal to 0
        query = select(RegisteredUsers).where(RegisteredUsers.createCount == 0)
        users = db.execute(query).scalars().all()

        if users:
            print(f"Found {len(users)} users who need a profile reminder.")
            for user in users:
                send_profile_reminder_email(user.email)
            print("Successfully sent all profile creation reminder emails.")
        else:
            print("No users found with a createCount of 0.")
    except Exception as e:
        print(f"An error occurred while sending profile reminders: {str(e)}")
    finally:
        db.close()

def tuesday_job():
    send_profile_creation_reminders()
    print("Tuesday job to send profile creation reminders has completed.")

def send_validation_reminder_emails():
    """
    Checks the NewUsers table and sends a validation reminder
    email to all users who have not been validated and have  been emailed yet.
    """
    db = SessionLocal()
    try:
        query = select(NewUsers)
        users = db.execute(query).scalars().all()

        if users:
            print(f"Found {len(users)} new users who need a validation reminder.")
            for user in users:
                send_validation_reminder_email(user.email)
            print("Successfully sent all new user validation reminder emails.")
        else:
            print("No new users found who need a validation reminder.")
    except Exception as e:
        print(f"An error occurred while sending new user reminders: {str(e)}")
    finally:
        db.close()

def thursday_job():
    send_validation_reminder_emails()
    print("Thursday job to send new user validation reminders has completed.")