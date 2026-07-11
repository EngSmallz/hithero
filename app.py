from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
import os, logging, datetime, base64, mimetypes, requests, threading
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine, Column, Integer, String, func, LargeBinary, DateTime, ForeignKey, UniqueConstraint, select, cast
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, relationship
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, cast, delete, insert, update
from typing import Optional, List
from tweepy import Client
from backend.core.settings import (
    BackendSettings,
    LOCAL_APP_ENVS,
    LOCAL_CORS_ORIGINS,
    PRODUCTION_CORS_ORIGINS,
    get_cors_allow_origins,
    session_cookie_https_only,
)
from backend.main import create_app
from backend.db.base import Base
from backend.db.session import (
    build_database_url,
    build_engine_kwargs,
    build_sql_server_url,
    create_database_resources,
    ensure_sqlite_database_directory,
)
from backend.db.models import (
    ForumComment,
    ForumPost,
    NewUsers,
    PasswordResetToken,
    PostVote,
    RegisteredUsers,
    School,
    Spotlight,
    TeacherList,
)
from backend.schemas.forum import CreatePostRequest, PostDisplay, PostUpdate, VoteInput
from backend.schemas.teachers import (
    TeacherDirectoryFilters,
    TeacherDirectoryResponse,
    TeacherDirectorySummary,
    TeacherProfileResponse,
)
from backend.routers.admin import create_admin_router
from backend.routers.forum import create_forum_router
from backend.routers.legacy import create_legacy_router, register_legacy_error_handlers
from backend.routers.profile import create_profile_router
from backend.routers.teachers import create_teacher_router
try:
    from azure.communication.email import EmailClient
except ImportError:
    EmailClient = None
try:
    import bleach
except ImportError:
    import html

    class _BleachFallback:
        @staticmethod
        def clean(value, tags=None, attributes=None, strip=False, protocols=None):
            return html.escape(value or "")

    bleach = _BleachFallback()

try:
    import puremagic
except ImportError:
    class _PuremagicFallback:
        @staticmethod
        def magic_buffer(_buffer):
            return []

    puremagic = _PuremagicFallback()

def detect_file_type(buffer):
    if hasattr(puremagic, "magic_string"):
        return puremagic.magic_string(buffer)
    return puremagic.magic_buffer(buffer)

load_dotenv()
logger = logging.getLogger(__name__)
settings = BackendSettings.from_environment()
APP_ENV = settings.app_env
app = create_app(settings)
limiter = app.state.limiter
RECAPTCHA_SECRET_KEY=os.getenv("SERVER_KEY_CAPTCHA")
TEST_RECAPTCHA_TOKEN = os.getenv("TEST_RECAPTCHA_TOKEN", "hithero-test-recaptcha")

# Forum formatting is intentionally limited to a small, sanitized HTML subset.
ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "p", "br"]
ALLOWED_ATTRS = {"a": ["href"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

###cronjob ip white list
CRONJOB_ALLOWED_IPS = {
    "116.203.129.16",
    "116.203.134.67",
    "23.88.105.37",
    "128.140.8.200",
    "91.99.23.109",
}


def sqlite_random_ordering():
    return func.random()


def database_random_ordering():
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        return sqlite_random_ordering()

    return func.newid()


# Construct SQLAlchemy database resources. Test/local imports must not depend
# on the production SQL Server configuration or create production-like tables.
database_resources = create_database_resources(APP_ENV)
SQLALCHEMY_DATABASE_URL = database_resources.database_url
engine = database_resources.engine
SessionLocal = database_resources.session_factory

# Maximum allowed file size in bytes (e.g., 1MB)
MAX_FILE_SIZE = 1 * 1024 * 1024

def init_db():
    Base.metadata.create_all(bind=engine)


if APP_ENV != "test":
    init_db()


#########functions############
def get_current_id(request: Request):
    return request.session.get("user_id", None)

def get_current_role(request: Request):
    return request.session.get("user_role", None)

def get_current_email(request: Request):
    return request.session.get("user_email", None)

def get_index_cookie(index: str, request: Request):
    return request.session.get(index, None)

def set_teacher_session(request: Request, teacher):
    request.session["state"] = teacher.state
    request.session["county"] = teacher.county
    request.session["district"] = teacher.district
    request.session["school"] = teacher.school
    request.session["teacher"] = teacher.name

def render_email_template(template_path: str, data: dict) -> str:
    """
    Loads an HTML template and replaces placeholders with provided data.
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Replace placeholders with data values
    for key, value in data.items():
        template_content = template_content.replace(f'{{{{ {key} }}}}', str(value))
    
    return template_content

def send_email(recipient_email: str, subject: str, html_message: str, plain_message: str): ###AZURE REPLACEMENT###
    """
    Sends an email using Azure Communication Services Email.
    """
    if APP_ENV == "test":
        print(f"APP_ENV=test; skipping email send to {recipient_email}.")
        return True

    if EmailClient is None:
        print("Azure email client is not installed. Skipping email send.")
        return False

    try:
        connection_string = os.getenv("AZURE_EMAIL_CONNECTION_STRING")
        sender_address = os.getenv("AZURE_EMAIL_SENDER")

        client = EmailClient.from_connection_string(connection_string)

        message = {
            "senderAddress": sender_address,
            "recipients": {
                "to": [{"address": recipient_email}]
            },
            "content": {
                "subject": subject,
                "html": html_message,
                "plainText": plain_message
            }
        }

        poller = client.begin_send(message)
        result = poller.result()

        print("Azure email sent:", result)
        return True

    except Exception as ex:
        print("Azure email error:", ex)
        return False

def send_attachment(recipient_email: str, subject: str, message: str, attachment_path: str):
    if APP_ENV == "test":
        print(f"APP_ENV=test; skipping attachment email to {recipient_email}.")
        return True

    if EmailClient is None:
        print("Azure email client is not installed. Skipping attachment email.")
        return False

    try:
        with open(attachment_path, "rb") as attachment:
            encoded_content = base64.b64encode(attachment.read()).decode("utf-8")

        content_type = mimetypes.guess_type(attachment_path)[0] or "application/octet-stream"
        client = EmailClient.from_connection_string(
            os.getenv("AZURE_EMAIL_CONNECTION_STRING")
        )
        email_message = {
            "senderAddress": os.getenv("AZURE_EMAIL_SENDER"),
            "recipients": {"to": [{"address": recipient_email}]},
            "content": {
                "subject": subject,
                "plainText": message,
                "html": f"<p>{message}</p>",
            },
            "attachments": [
                {
                    "name": os.path.basename(attachment_path),
                    "contentType": content_type,
                    "contentInBase64": encoded_content,
                }
            ],
        }
        return client.begin_send(email_message).result()
    except Exception as ex:
        print("Azure attachment email error:", ex)
        return False

def send_registration_email(recipient_email: str):
    """
    Prepares and sends the registration success email using the HTML template.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "Thank you for registering with us! Once you are validated by a "
            "fellow teacher in your district or one of us here at Homeroom Heroes, "
            "you will be able to create your profile and start receiving support."
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Registration successful",
        html_message,
        plain_message
    )

def send_validation_email(recipient_email: str):
    """
    Prepares and sends the validation success email using the HTML template.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "We are pleased to inform you that your registration with us has been "
            "successfully validated! You may now log in and create your profile "
            "to start receiving support."
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Validation Notification",
        html_message,
        plain_message
    )

def update_temp_password(db: Session, email: str, new_password: str):
    try:
        hashed_password = sha256_crypt.hash(new_password)
        query = update(RegisteredUsers).where(cast(RegisteredUsers.email, String) == cast(email, String)).values(password=hashed_password)
        db.execute(query)
        db.commit()  
    except Exception as e:
        print(f"Error updating password: {e}")
        raise

# Function to fetch a random teacher from the database
def fetch_random_teacher():
    db = SessionLocal()
    try:
        # The scalar_one_or_none() method directly returns the TeacherList object,
        # or None if no teacher is found.
        query = select(TeacherList).order_by(database_random_ordering()).limit(1)
        random_teacher_record = db.execute(query).scalar_one_or_none()
        return random_teacher_record
    except Exception as e:
        print(f"Error fetching random teacher: {e}")
        return None
    finally:
        db.close()

def store_spotlight(teacher_info: dict, token: str):
    db = SessionLocal()
    try:
        delete_query = delete(Spotlight).where(cast(Spotlight.token, String) == cast(token, String))
        db.execute(delete_query)
        if token == "teacher":
            spotlight_entry = Spotlight(state=teacher_info["state"],county=teacher_info["county"],district=teacher_info["district"],school=teacher_info["school"],name=teacher_info["name"],token=token,image_data=teacher_info["image_data"] )
        elif token == "district":
            spotlight_entry = Spotlight(state=teacher_info["state"],county=teacher_info["county"],district=teacher_info["district"],token=token)
        elif token == "county":
            spotlight_entry = Spotlight(state=teacher_info["state"],county=teacher_info["county"],token=token)
        db.add(spotlight_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def send_teacher_of_the_day_email(recipient_email: str, recipient_name: str, url_id: str):
    """
    Prepares and sends the 'Teacher of the Day' notification email.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_name,
        'message_body': (
            "Congratulations! You've been chosen as today's 'Teacher of the Day' at Homeroom Heroes! "
            "Your profile is now featured on our homepage, giving you extra visibility. "
            "Remember to share your unique page with your community. "
            f"www.HelpTeachers.net/teacher/{url_id}"
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "🎉 You're Today's Homeroom Hero!",
        html_message,
        plain_message
    )

def daily_job():
    db = SessionLocal()
    try:
        # Re-fetch the teacher to ensure we get the full object with regUserID and url_id
        random_teacher = fetch_random_teacher()
        
        if random_teacher:
            teacher_info = {
                "name": random_teacher.name, 
                "state": random_teacher.state,
                "county": random_teacher.county,
                "district": random_teacher.district,
                "school": random_teacher.school,
                "image_data": random_teacher.image_data,
                "url_id": random_teacher.url_id
            }

            # Store the teacher in the spotlight regardless of email availability
            store_spotlight(teacher_info, "teacher")

            # Now, attempt to fetch the email and send the notification
            email_query = select(RegisteredUsers.email).where(RegisteredUsers.id == random_teacher.regUserID)
            teacher_email = db.execute(email_query).scalar_one_or_none()

            # Now make x post about the teacher <-- REPLACE THIS COMMENT WITH THE FOLLOWING LINES
            teacher_url = f"www.HelpTeachers.net/teacher/{random_teacher.url_id}"
            tweet_message = (
                f"Today's #TeacherOfTheDay is {random_teacher.name}! "
                f"You can support their classroom and mission here: {teacher_url}"
                f"#HomeroomHeroes #Education"
            )
            post_tweet_x(tweet_message)

            if teacher_email:
                # Send the email notification
                send_teacher_of_the_day_email(
                    recipient_email=teacher_email,
                    recipient_name=teacher_info["name"],
                    url_id=teacher_info["url_id"]
                )
            else:
                print(f"No email found for teacher: {random_teacher.name}. Spotlight stored, but no email sent.")
        else:
            print("No random teacher found.")
    except Exception as e:
        print(f"Error in daily_job: {e}")
    finally:
        db.close()

def monday_job():
    random_teacher = fetch_random_teacher()
    if random_teacher:
        teacher_info = {
            "state": random_teacher[0].state,
            "county": random_teacher[0].county,
            "district": random_teacher[0].district,
        }
        store_spotlight(teacher_info, "district")
    else:
        print("No random teacher found.")

def first_of_month_job():
    if date.today().day == 1:
        random_teacher = fetch_random_teacher()
        if random_teacher:
            teacher_info = {
                "state": random_teacher[0].state,
                "county": random_teacher[0].county
            }
            store_spotlight(teacher_info, "county")
        else:
            print("No random teacher found.")
    else:
        print('Not the first.')

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

######   EMAILER FUNCTIONS FOR CRONJOBS  ###########
def verify_cronjob_request(request: Request):
    secret = request.headers.get("x-secret-key")
    if not secret or secret != os.getenv("INTERNAL_JOB_SECRET"):
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/internal/run-wednesday-job")
async def run_wednesday_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=wednesday_job, daemon=True).start()
    return {"status": "wednesday job started"}

@app.post("/internal/run-tuesday-job")
async def run_tuesday_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=tuesday_job, daemon=True).start()
    return {"status": "tuesday job started"}

@app.post("/internal/run-thursday-job")
async def run_thursday_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=thursday_job, daemon=True).start()
    return {"status": "thursday job started"}

@app.post("/internal/run-daily-job")
async def run_daily_job(request: Request, _: None = Depends(verify_cronjob_request)):
    threading.Thread(target=daily_job, daemon=True).start()
    return {"status": "daily job started"}


#####################################################



def verify_recaptcha(recaptcha_response: str):
    """Verifies the reCAPTCHA response with Google's servers."""
    if APP_ENV == "test":
        return recaptcha_response == TEST_RECAPTCHA_TOKEN

    url = "https://www.google.com/recaptcha/api/siteverify"
    params = {"secret": RECAPTCHA_SECRET_KEY, "response": recaptcha_response}
    response = requests.post(url, params=params)
    data = response.json()
    return data.get("success", False)

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

def send_profile_reminder_email(recipient_email: str):
    """
    Sends a reminder email to a user to complete their profile.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "You're almost there! Your registration with us has been "
            "successfully validated, but you haven't created your profile yet. "
            "Please log in and complete your profile to start receiving support from our community.\n"
            "www.HelpTeachers.net/login"
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Reminder: Complete Your Homeroom Heroes Profile!",
        html_message,
        plain_message
    )

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

def send_validation_reminder_email(recipient_email: str):
    """
    Sends a reminder email to a new user to reach out for validation.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "Thanks for signing up! We noticed you haven't been validated yet. "
            "Please reach back out to us at homeroom.heroes.contact@gmail.com to complete your validation process."
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Reminder: Complete Your Homeroom Heroes Validation!",
        html_message,
        plain_message
    )

def thursday_job():
    send_validation_reminder_emails()
    print("Thursday job to send new user validation reminders has completed.")

def post_tweet_x(tweet_text: str):
    """
    Authenticates and posts a tweet using the X API (Tweepy v2).
    REQUIRES: Consumer Key, Consumer Secret, Access Token, and Access Token Secret.
    These must be stored securely as environment variables.
    """
    API_KEY = os.getenv("X_API_KEY")
    API_SECRET = os.getenv("X_API_SECRET")
    ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
    ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("X API credentials missing. Skipping tweet post.")
        print("Please set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET environment variables.")
        return
    try:
        # Authenticate using OAuth 1.0a (required for posting tweets)
        client = Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET
        )
        # Post the tweet
        response = client.create_tweet(text=tweet_text)
        print(f"X POST SUCCESS: Tweeted: {tweet_text}")
        print(f"X Response ID: {response.data['id']}")
    except Exception as e:
        print(f"X POST ERROR: Failed to post tweet. {e}")

def model_to_dict(model):
    """Converts a SQLAlchemy model instance to a dictionary, handling dates for JSON serialization."""
    data = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        # Convert datetime objects to ISO format string
        if hasattr(value, 'isoformat'):
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data


##api gets a random teacher from the list teacher_list in the hithero data base

@app.get("/api/random_teacher/")
async def get_random_teacher(request: Request):
    try:
        teacher = fetch_random_teacher()
        if not teacher:
            raise HTTPException(status_code=404, detail="No teachers found in the database")
        if teacher.image_data:
            image_data = base64.b64encode(teacher.image_data).decode('utf-8')
        else:
            image_data = None
        data = {
            "name": teacher.name,
            "state": teacher.state,
            "county": teacher.county,
            "district": teacher.district,
            "school": teacher.school,
            "image_data": image_data
        }
        if hasattr(request, "session"):
            set_teacher_session(request, teacher)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")


## api used to send contact us email from /contact.html
@app.post('/api/contact_us/')
async def contact_us(name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...), recaptcha_response: str = Form(...)):

    # reCAPTCHA verification
    is_valid = verify_recaptcha(recaptcha_response)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")

    #clean and Define the data to populate the template
    clean_name = bleach.clean(name, tags=[], attributes={}, strip=True)
    clean_email = bleach.clean(email, tags=[], attributes={}, strip=True)
    clean_message = bleach.clean(message, tags=[], attributes={}, strip=True)
    clean_subject = bleach.clean(subject, tags=[], attributes={}, strip=True)

    template_data = {
        'recipient_name': 'Homeroom Heroes Team',
        'message_body': f"Message from {clean_name} ({clean_email}):\n\n{clean_message}"
    }

    # 1. Generate the HTML message from the template
    # The path is correctly specified relative to the project root
    html_message = render_email_template('static/email_template.html', template_data)

    # 2. Create a plain text fallback version
    plain_message = (
        f"Subject: {clean_subject}\n"
        f"Message from {clean_name} ({clean_email}):\n\n"
        f"{clean_message}"
    )

    recipient_email = 'Homeroom.heroes.contact@gmail.com'
    try:
        send_email(recipient_email, clean_subject, html_message, plain_message)
        return {"message": "Email sent successfully!"}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")

app.include_router(
    create_legacy_router(
        session_factory=SessionLocal,
        teacher_model=TeacherList,
        spotlight_model=Spotlight,
        set_teacher_session=set_teacher_session,
        logger=logger,
    )
)
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
register_legacy_error_handlers(app)

app.include_router(
    create_teacher_router(
        session_factory=SessionLocal,
        school_model=School,
        teacher_model=TeacherList,
        directory_response_model=TeacherDirectoryResponse,
        profile_response_model=TeacherProfileResponse,
    )
)

app.include_router(
    create_forum_router(
        session_factory=SessionLocal,
        post_model=ForumPost,
        comment_model=ForumComment,
        vote_model=PostVote,
        vote_input_model=VoteInput,
        post_update_model=PostUpdate,
        get_current_id=get_current_id,
        get_current_role=get_current_role,
        limiter=limiter,
        clean_html=bleach.clean,
        allowed_tags=ALLOWED_TAGS,
        allowed_attrs=ALLOWED_ATTRS,
        allowed_protocols=ALLOWED_PROTOCOLS,
        model_to_dict=model_to_dict,
    )
)

app.include_router(
    create_profile_router(
        session_factory=SessionLocal,
        pending_user_model=NewUsers,
        registered_user_model=RegisteredUsers,
        teacher_model=TeacherList,
        reset_token_model=PasswordResetToken,
        get_current_id=get_current_id,
        get_current_role=get_current_role,
        get_current_email=get_current_email,
        get_index_cookie=get_index_cookie,
        set_teacher_session=set_teacher_session,
        verify_recaptcha=verify_recaptcha,
        send_registration_email=send_registration_email,
        render_email_template=render_email_template,
        send_email=send_email,
        limiter=limiter,
        detect_file_type=detect_file_type,
        max_file_size=MAX_FILE_SIZE,
        logger=logger,
    )
)

app.include_router(
    create_admin_router(
        session_factory=SessionLocal,
        pending_user_model=NewUsers,
        registered_user_model=RegisteredUsers,
        teacher_model=TeacherList,
        get_current_id=get_current_id,
        get_current_role=get_current_role,
        set_teacher_session=set_teacher_session,
        get_index_cookie=get_index_cookie,
        send_validation_email=send_validation_email,
        send_attachment=send_attachment,
        logger=logger,
        get_admin_secret=os.getenv,
    )
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
