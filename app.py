from fastapi import FastAPI, HTTPException, Request, Form, Depends, Body, File, UploadFile, Response, status, Path
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from pydantic import BaseModel, Field
import os, logging, smtplib, secrets, string, time, ssl, datetime, base64, requests, threading
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine, Column, Integer, String, func, LargeBinary, DateTime, ForeignKey, UniqueConstraint, select, desc, cast
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, cast, delete, insert, update
from typing import Optional, List
from tweepy import Client
from backend.routers.teachers import create_teacher_router
try:
    from azure.communication.email import EmailClient
except ImportError:
    EmailClient = None
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
except ImportError:
    class RateLimitExceeded(Exception):
        pass

    def _rate_limit_exceeded_handler(request, exc):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    def get_remote_address(request):
        client = getattr(request, "client", None)
        return client.host if client else "testclient"

    class Limiter:
        def __init__(self, key_func):
            self.key_func = key_func

        def limit(self, _limit):
            def decorator(func):
                return func
            return decorator
import re
try:
    import bleach
except ImportError:
    import html

    class _BleachFallback:
        @staticmethod
        def clean(value, tags=None, attributes=None, strip=False):
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

app = FastAPI()
load_dotenv()
logger = logging.getLogger(__name__)
APP_ENV = os.getenv("APP_ENV", "").lower()
LOCAL_APP_ENVS = {"dev", "development", "local"}


PRODUCTION_CORS_ORIGINS = ["https://www.helpteachers.net", "https://helpteachers.net"]
LOCAL_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


def get_cors_allow_origins(app_env: str):
    configured_origins = os.getenv("CORS_ALLOW_ORIGINS")
    if configured_origins:
        return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

    origins = list(PRODUCTION_CORS_ORIGINS)
    if app_env == "test" or app_env in LOCAL_APP_ENVS:
        origins.extend(LOCAL_CORS_ORIGINS)

    return origins


def session_cookie_https_only(app_env: str):
    return app_env != "test" and app_env not in LOCAL_APP_ENVS


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    https_only=session_cookie_https_only(APP_ENV),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allow_origins(APP_ENV),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
RECAPTCHA_SECRET_KEY=os.getenv("SERVER_KEY_CAPTCHA")
TEST_RECAPTCHA_TOKEN = os.getenv("TEST_RECAPTCHA_TOKEN", "hithero-test-recaptcha")

##limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Disable documentation routes
app.openapi_url = None
app.redoc_url = None

###content cleanup and formatting for forum
ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "p", "br"]
ALLOWED_ATTRS = {"a": ["href"]}

# Determine the path to the directory
app.mount("/static", StaticFiles(directory="static"), name="static")
BASE_STATIC_DIR = "static"
PAGES_DIR = "pages"

PUBLIC_PAGE_ALIASES = {
    "/": "homepage.html",
    "/home": "homepage.html",
    "/about": "about.html",
    "/contact": "contact.html",
    "/partners": "partners.html",
    "/register": "register.html",
    "/login": "login.html",
    "/forgot": "forgot.html",
    "/update-password": "update_password.html",
    "/reset-password": "reset_password.html",
    "/wishlist-setup": "wishlist_setup.html",
    "/terms": "terms_conditions.html",
    "/teachers": "index.html",
    "/403": "403.html",
    "/404": "404.html",
}

PRIVATE_PAGE_ALIASES = {
    "/forum": "forum.html",
    "/forum/new": "create_post.html",
    "/forum/post": "post.html",
    "/teacher": "teacher.html",
    "/validation": "validation.html",
    "/admin": "admin.html",
    "/profile/create": "create.html",
    "/profile/edit": "edit_teacher.html",
}

LEGACY_PUBLIC_PAGE_REDIRECTS = {
    "/pages/homepage.html": "/",
    "/pages/index.html": "/teachers",
    "/pages/about.html": "/about",
    "/pages/contact.html": "/contact",
    "/pages/partners.html": "/partners",
    "/pages/register.html": "/register",
    "/pages/login.html": "/login",
    "/pages/forgot.html": "/forgot",
    "/pages/terms_conditions.html": "/terms",
    "/pages/403.html": "/403",
    "/pages/404.html": "/404",
}

PAGE_ROUTE_METHODS = ["GET", "HEAD"]

ADS_TXT_PATH = f"{BASE_STATIC_DIR}/ads.txt"
SITEMAP_XML_PATH = f"{BASE_STATIC_DIR}/sitemap.xml"


def serve_page(page_name: str, status_code: int = 200) -> FileResponse:
    return FileResponse(os.path.join(PAGES_DIR, page_name), status_code=status_code)

# 1. Route for ads.txt (media_type='text/plain')
@app.get("/ads.txt", include_in_schema=False)
async def get_ads_txt():
    """Serves ads.txt from the static folder at the root URL."""
    return FileResponse(ADS_TXT_PATH, media_type='text/plain')

# 2. Route for sitemap.xml (media_type='application/xml')
@app.get("/sitemap.xml", include_in_schema=False)
async def get_sitemap_xml():
    """Serves sitemap.xml from the static folder at the root URL."""
    return FileResponse(SITEMAP_XML_PATH, media_type='application/xml')

# --- Configuration for Promotional Images Mapping ---
PROMO_IMAGE_MAPPING = {
    "seattlewolf": "images/partners/1007TheWolf.png",
    "livefree": "images/partners/965CountryColor.png",
    "basecamp": "images/partners/BaseCamp.png",
    "coastal": "images/partners/Coastal.png"
}

###cronjob ip white list
CRONJOB_ALLOWED_IPS = {
    "116.203.129.16",
    "116.203.134.67",
    "23.88.105.37",
    "128.140.8.200",
    "91.99.23.109",
}


# Load environment variables
DATABASE_SERVER = os.getenv("DATABASE_SERVER")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_UID = os.getenv("DATABASE_UID")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")

def build_sql_server_url():
    return f"mssql+pyodbc://{DATABASE_UID}:{DATABASE_PASSWORD}@{DATABASE_SERVER}:{DATABASE_PORT}/{DATABASE_NAME}?driver=ODBC+Driver+18+for+SQL+Server"


def build_database_url(app_env: str):
    explicit_database_url = os.getenv("DATABASE_URL")
    if explicit_database_url:
        return explicit_database_url

    if app_env == "test":
        return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    if app_env in LOCAL_APP_ENVS:
        return os.getenv("LOCAL_DATABASE_URL", "sqlite:///./.local/hithero-dev.sqlite")

    return build_sql_server_url()


def ensure_sqlite_database_directory(database_url: str):
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        return

    database_directory = os.path.dirname(os.path.abspath(url.database))
    if database_directory:
        os.makedirs(database_directory, exist_ok=True)


def build_engine_kwargs(database_url: str):
    url = make_url(database_url)
    engine_options = {}

    if url.drivername.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if url.database == ":memory:":
            engine_options["poolclass"] = StaticPool

    return engine_options


def sqlite_random_ordering():
    return func.random()


def database_random_ordering():
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        return sqlite_random_ordering()

    return func.newid()


# Construct SQLAlchemy database URL. Test/local imports must not depend on the
# production SQL Server configuration or create production-like tables.
SQLALCHEMY_DATABASE_URL = build_database_url(APP_ENV)
ensure_sqlite_database_directory(SQLALCHEMY_DATABASE_URL)

engine = create_engine(SQLALCHEMY_DATABASE_URL, **build_engine_kwargs(SQLALCHEMY_DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Maximum allowed file size in bytes (e.g., 1MB)
MAX_FILE_SIZE = 1 * 1024 * 1024

# Define SQLAlchemy models
class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True)
    school_name = Column(String)
    district = Column(String)
    county = Column(String)
    state = Column(String)

class NewUsers(Base):
    __tablename__ = "new_users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    state = Column(String)
    county = Column(String)
    district = Column(String)
    school = Column(String)
    phone_number = Column(String)
    password = Column(String)
    role = Column(String)
    report = Column(Integer)
    emailed = Column(Integer)

class RegisteredUsers(Base):
    __tablename__ = "registered_users"

    id = Column(Integer, primary_key=True)
    email = Column(String)
    phone_number = Column(String)
    password = Column(String)
    role = Column(String)
    createCount = Column(Integer)

class TeacherList(Base):
    __tablename__ = "teacher_list"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    state = Column(String)
    county = Column(String)
    district = Column(String)
    school = Column(String)
    regUserID = Column(Integer)
    wishlist_url = Column(String)
    about_me = Column(String)
    image_data = Column(LargeBinary)
    url_id = Column(String)

class Spotlight(Base):
    __tablename__ = "spotlight"

    id = Column(Integer, primary_key=True)
    token = Column(String)
    name = Column(String)
    state = Column(String)
    county = Column(String)
    district = Column(String)
    school = Column(String)
    image_data = Column(LargeBinary)

class ForumPost(Base):
    __tablename__ = "forum_posts"

    # Core Post Data
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=False)
    
    # User and Timestamp
    user_id = Column(Integer, ForeignKey("registered_users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Denormalized/Cached Metrics (for fast sorting/display)
    upvote_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)


class ForumComment(Base):
    __tablename__ = "forum_comments"

    # Core Comment Data
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    
    # Relationships
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("registered_users.id"), nullable=False)
    
    # Hierarchy and Timestamp
    parent_comment_id = Column(Integer, ForeignKey("forum_comments.id"), nullable=True) # For nested replies
    created_at = Column(DateTime, default=func.now(), nullable=False)


class PostVote(Base):
    __tablename__ = "post_votes"

    # Core Vote Data
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("registered_users.id"), nullable=False)
    
    # 1 for Upvote, -1 for Downvote
    vote_type = Column(Integer, nullable=False) 

    # Enforce uniqueness: a user can only vote on a post once
    __table_args__ = (UniqueConstraint('post_id', 'user_id', name='uq_post_user_vote'), )
    
class CreatePostRequest(BaseModel):
    """Defines the expected input structure for creating a new forum post."""
    title: str
    content: str

class PostDisplay(BaseModel):
    """Schema for returning post data."""
    id: int
    title: str
    content: str
    user_id: int
    created_at: datetime.datetime
    upvote_count: int
    comment_count: int

    class Config:
        from_attributes = True

class VoteInput(BaseModel):
    """Defines the expected input structure for posting a vote."""
    vote_type: int = Field(..., description="1 for Upvote, -1 for Downvote")

class TeacherDirectorySummary(BaseModel):
    name: str
    url_id: str
    state: Optional[str] = None
    county: Optional[str] = None
    district: Optional[str] = None
    school: Optional[str] = None

class TeacherDirectoryFilters(BaseModel):
    states: List[str]
    counties: List[str]
    districts: List[str]
    schools: List[str]

class TeacherDirectoryResponse(BaseModel):
    teachers: List[TeacherDirectorySummary]
    filters: TeacherDirectoryFilters
    total: int
    applied_filters: dict[str, Optional[str]]

class TeacherProfileResponse(BaseModel):
    name: str
    url_id: str
    state: Optional[str] = None
    county: Optional[str] = None
    district: Optional[str] = None
    school: Optional[str] = None
    wishlist_url: Optional[str] = None
    about_me: Optional[str] = None
    image_data: Optional[str] = None

class PostUpdate(BaseModel):
    """Schema for the data received when updating a post."""
    title: str
    content: str

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Integer, default=0)

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

def teacher_session_response(teacher):
    return {
        "state": teacher.state,
        "county": teacher.county,
        "district": teacher.district,
        "school": teacher.school,
        "teacher": teacher.name,
    }

def store_my_cookies(request: Request, id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(TeacherList.regUserID == id)
        result = db.execute(query)
        teacher_data = result.fetchone()
        if teacher_data:
            set_teacher_session(request, teacher_data[0])
        else:
            raise HTTPException(status_code=404, detail="Your account does not have a database listing")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

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


#######apis#######
###api used to register a new user (and only a new user) into the new_user list
@app.post("/profile/register/")
@limiter.limit("5/minute")
async def register_user(request: Request, name: str = Form(...), email: str = Form(...), phone_number: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), state: str = Form(...),county: str = Form(...),district: str = Form(...), school: str = Form(...), recaptcha_response: str = Form(...)):
    # Verify reCAPTCHA
    if not verify_recaptcha(recaptcha_response):
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed. Please try again.")

    db = SessionLocal()
    try:
        query = select(RegisteredUsers.id).where(cast(RegisteredUsers.email, String) == cast(email, String))
        result = db.execute(query)
        existing_user = result.fetchone()
        if existing_user:
            return {"message": "User with this email already exists."}
        query = select(NewUsers.id).where(cast(NewUsers.email, String) == cast(email, String))
        result = db.execute(query)
        existing_user = result.fetchone()
        if existing_user:
            return {"message": "User with this email is already in the registration queue."}
        if password != confirm_password:
            return {"message": "Password do not match."}
        hashed_password = sha256_crypt.hash(password)
        role = 'teacher'
        new_user = NewUsers(name=name, email=email, state=state, county=county, district=district, school=school, phone_number=phone_number, password=hashed_password, role=role, report=0, emailed=0)
        db.add(new_user)
        db.commit()
        send_registration_email(email)
        return {"message": "User registered successfully. You should recieve an email shortly. Please check your spam folder"}
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {"message": "Registration unsuccessful. Please try again later."}

    
###api used to create cookie based session via authentication with registered_user table
@app.post("/profile/login/")
@limiter.limit("5/minute")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        query = select(RegisteredUsers).where(cast(RegisteredUsers.email, String) == cast(email, String))
        result = db.execute(query)
        user = result.fetchone()
        if user:
            hashed_password = user[0].password
            if sha256_crypt.verify(password, hashed_password):
                message = "Login successful as " + user[0].role
                request.session["user_email"] = email
                request.session["user_role"] = user[0].role
                request.session["user_id"] = user[0].id
                return JSONResponse(content={"message": message, "createCount": user[0].createCount, "role": user[0].role})
            else:
                message = "Invalid login credentials."
        else:
            message = "Invalid login credentials."
        return JSONResponse(content={"message": message})
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##end cookie session
@app.post("/profile/logout/")
async def logout_user(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
        del request.session["user_role"]
        del request.session["user_email"]
    return RedirectResponse(url="/", status_code=303)

# Endpoint to move a user from new_users to registered_users and delete item in new_users
@app.post("/validation/validate_user/{user_email}")
async def move_user(user_email: str, role: str = Depends(get_current_role), request: Request = None):
    if role not in ('admin', 'teacher'):
        raise HTTPException(status_code=403, detail="Access denied.")
    db = SessionLocal()
    try:
        query = select(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
        result = db.execute(query)
        user = result.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in new_users")

        # Teachers can only validate users within their own district
        if role == 'teacher':
            id = get_current_id(request)
            teacher_record = db.execute(select(TeacherList).where(TeacherList.regUserID == id)).fetchone()
            if not teacher_record or (
                user[0].state != teacher_record[0].state or
                user[0].county != teacher_record[0].county or
                user[0].district != teacher_record[0].district
            ):
                raise HTTPException(status_code=403, detail="You can only validate teachers in your own district.")
        
        query = insert(RegisteredUsers).values(email=user[0].email, password=user[0].password, role=user[0].role, phone_number = user[0].phone_number)
        db.execute(query)
        delete_query = delete(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
        db.execute(delete_query)
        db.commit()
        send_validation_email(user[0].email)        
        return {"message": "User validated."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##this api allows a logged in user to create an item in the table teacher_list in the hithero database if they have not created a user already
@app.post("/profile/create_teacher_profile/")
async def create_teacher_profile(request: Request, name: str = Form(...), state: str = Form(...), county: str = Form(...), district: str = Form(...), school: str = Form(...), aboutMe: str = Form(...), wishlist: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            query = select(RegisteredUsers.createCount).where(RegisteredUsers.id == id)
            result = db.execute(query)
            create_count = result.scalar()
            if create_count == 0 or role == 'admin':
                aa_link = wishlist + "&tag=h0mer00mher0-20" 
                email = get_current_email(request)
                first_part_email = email.split('@')[0]
                random_number = secrets.randbelow(9999)
                auto_url_id = f"{first_part_email}{random_number}"
                while db.execute(select(TeacherList).where(cast(TeacherList.url_id, String) == cast(auto_url_id, String))).first():
                    random_number = secrets.randbelow(9999)
                    auto_url_id = f"{first_part_email}{random_number}"

                insert_query = insert(TeacherList).values(
                    name=name,
                    state=state,
                    county=county,
                    district=district,
                    school=school,
                    regUserID=id,
                    about_me=aboutMe,
                    wishlist_url=aa_link,
                    url_id=auto_url_id
                )
                db.execute(insert_query)
                update_query = update(RegisteredUsers).where(RegisteredUsers.id == id).values(createCount=RegisteredUsers.createCount + 1)
                db.execute(update_query)
                db.commit()
                return {"message": "Teacher created successfully", "role": role}
            else:
                return {"message": "Unable to create new profile. Profile already created."}
        else:
            return {"message": "No user logged in."}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

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
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")


###api gets the current session info of the logged in user
@app.get("/api/profile/")
async def get_user_profile(email: str = Depends(get_current_email), role: str = Depends(get_current_role), id: str = Depends(get_current_id)):
    if email:
        user_info = {
            "user_id": id,
            "user_role": role,
            "user_email": email
        }
        return JSONResponse(content=user_info)
    else:
        raise HTTPException(status_code=404, detail="No user logged in.")


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

for route_path, page_name in PUBLIC_PAGE_ALIASES.items():
    async def public_page_alias(_request: Request, page_name: str = page_name):
        return serve_page(page_name)

    app.add_api_route(route_path, public_page_alias, methods=PAGE_ROUTE_METHODS, include_in_schema=False)


for route_path, page_name in PRIVATE_PAGE_ALIASES.items():
    async def private_page_alias(_request: Request, page_name: str = page_name):
        return serve_page(page_name)

    app.add_api_route(route_path, private_page_alias, methods=PAGE_ROUTE_METHODS, include_in_schema=False)


for legacy_path, clean_path in LEGACY_PUBLIC_PAGE_REDIRECTS.items():
    async def legacy_public_page_redirect(_request: Request, clean_path: str = clean_path):
        return RedirectResponse(url=clean_path, status_code=307)

    app.add_api_route(legacy_path, legacy_public_page_redirect, methods=PAGE_ROUTE_METHODS, include_in_schema=False)


app.mount("/pages", StaticFiles(directory="pages"), name="pages")


# Custom 404 error handler
@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return serve_page("404.html", status_code=404)

# Custom 403 error handler
@app.exception_handler(403)
async def forbidden(request: Request, exc: HTTPException):
    return serve_page("403.html", status_code=403)

###api gets a teacher data from teacher_list table
@app.get("/api/get_teacher_info/")
async def get_teacher_info(request: Request):
    db = SessionLocal()
    try:
        state = get_index_cookie('state', request)
        county = get_index_cookie('county', request)
        district = get_index_cookie('district', request)
        school = get_index_cookie('school', request)
        name = get_index_cookie('teacher', request)
        query = select(TeacherList).where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county) &
            (cast(TeacherList.district, String) == district) &
            (cast(TeacherList.school, String) == school) &
            (cast(TeacherList.name, String) == name)
        )
        result = db.execute(query)
        teacher_info = result.fetchone()
        if teacher_info:
            if teacher_info[0].image_data:
                image_data = base64.b64encode(teacher_info[0].image_data).decode('utf-8')
            else:
                image_data = None
            data = {
                "state": teacher_info[0].state,
                "county": teacher_info[0].county,
                "district": teacher_info[0].district,
                "school": teacher_info[0].school,
                "name": teacher_info[0].name,
                "wishlist_url": teacher_info[0].wishlist_url,
                "about_me": teacher_info[0].about_me,
                "image_data": image_data
            }
            return data
        else:
            raise HTTPException(status_code=404, detail="Teacher not found")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api that updates about me info
@app.post("/profile/update_info/")
async def update_info(request: Request, aboutMe: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(about_me=aboutMe)
            db.execute(update_query)
            db.commit()
            return {"message": "Info updated."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api that updates school
@app.post("/profile/update_teacher_school/")
async def update_teacher_school(
    request: Request,
    state: str = Form(...),
    county: str = Form(...),
    district: str = Form(...),
    school: str = Form(...),
    id: int = Depends(get_current_id),
    role: str = Depends(get_current_role)
):
    db: Session = SessionLocal()
    try:
        if role:
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(
                state=state,
                county=county,
                district=district,
                school=school
            )
            db.execute(update_query)
            db.commit()
            return JSONResponse(content={"message": "School information updated successfully."})
        else:
            raise HTTPException(status_code=403, detail="Permission denied. Not logged in.")
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api that updates name
@app.post("/profile/update_teacher_name/")
async def update_teacher_name(request: Request, teacher: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(name=teacher)
            db.execute(update_query)
            db.commit()
            return {"message": "Name updated."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api to update wishlist
@app.post("/profile/update_wishlist/")
async def update_wishlist(request: Request, wishlist: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            aa_link = wishlist + "&tag=h0mer00mher0-20"
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(wishlist_url=aa_link)
            db.execute(update_query)
            db.commit()
            return {"message": "Wishlist updated."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()


#api that update the url of a teachers page
@app.post("/profile/update_url_id/")
async def update_url_id(request: Request, url_id: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', url_id):
                raise HTTPException(status_code=400, detail="URL ID may only contain letters, numbers, hyphens, and underscores (3–50 characters).")
            existing_teacher = db.query(TeacherList).where(cast(TeacherList.url_id, String) == cast(url_id, String)).first()
            if existing_teacher:
                raise HTTPException(status_code=409, detail="URL ID already in use.")
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(url_id=url_id)
            db.execute(update_query)
            db.commit()
            return {"message": "URL ID updated successfully."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

    
###api used to update the logged in users teacher page image
@app.post("/profile/update_teacher_image/")
async def edit_teacher_image(request: Request, role: str = Depends(get_current_role), image: UploadFile = Form(...), id: int = Depends(get_current_id)):
    db: Session = SessionLocal()
    try:
        if image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds the allowed limit")
        
        # Read bytes once, then use for both magic check and DB storage
        image_bytes = await image.read()
        
        # Validate by actual file signature, not client-supplied content_type
        ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        
        # puremagic equivalent to magic.from_buffer(..., mime=True)
        results = puremagic.magic_buffer(image_bytes)
        
        # Grab the mime type from the first (best) match
        detected_type = results[0].mime if results else None

        if detected_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
        
        if role:
            update_query = update(TeacherList).values(image_data=image_bytes).where(
                TeacherList.regUserID == id
            )
            db.execute(update_query)
            db.commit()
            return {"message": "Information updated."}
        else:
            return {"message": "Permission denied."}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()


##api gets your page based on the id in reg_users and and regUserID in teacher_list
@app.get("/profile/myinfo/")
async def get_myinfo(request: Request, id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(TeacherList.regUserID == id)
        result = db.execute(query)
        teacher_data = result.fetchone()
        if teacher_data:
            set_teacher_session(request, teacher_data[0])
            return teacher_session_response(teacher_data[0])
        else:
            return {"message": "Your account does not have a database listing"}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()


##api lets the logged in user update their password
@app.post("/profile/update_password/")
async def update_password(request: Request, id: int = Depends(get_current_id), old_password: str = Form(...), new_password: str = Form(...), new_password_confirmed: str = Form(...)):
    db = SessionLocal()
    try:
        if new_password == new_password_confirmed:
            query = select(RegisteredUsers.password).where(RegisteredUsers.id == id)
            result = db.execute(query)
            old_pass = result.scalar()
            if old_pass and sha256_crypt.verify(old_password, old_pass):
                hashed_new_password = sha256_crypt.hash(new_password)
                update_query = update(RegisteredUsers).where(RegisteredUsers.id == id).values(password=hashed_new_password)
                db.execute(update_query)
                db.commit()
                return {"status": "success", "message": "Password updated successfully"}
            else:
                return {"message": "Invalid old password"}
        else:
            return {"message": "New passwords do not match."}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()


#api to check if a user has edit acces to teacher page
@app.get("/api/check_access_teacher/")
async def check_access_teacher(request: Request, id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role == 'teacher':
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie('school', request)
            name = get_index_cookie('teacher', request)
            query = select(TeacherList.regUserID).where(
                (cast(TeacherList.state, String) == state) &
                (cast(TeacherList.county, String) == county) &
                (cast(TeacherList.district, String) == district) &
                (cast(TeacherList.school, String) == school) &
                (cast(TeacherList.name, String) == name)
            )
            result = db.execute(query)
            teacher_data = result.scalar()
            if teacher_data == id:
                return {"status": "success", "message": "Access granted"}
        raise HTTPException(status_code=403, detail="No access")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()


#gets a list of unverified users to validate based on the role of the user
@app.get("/api/validation_list/")
async def validation_page(request: Request, role: str = Depends(get_current_role), id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        if role == "admin":
            query = select(NewUsers)
            result = db.execute(query)
            new_users = result.fetchall()
            return {"new_users": [{"name": user[0].name, "email": user[0].email, "state": user[0].state, "district": user[0].district, "school": user[0].school, "phone_number": user[0].phone_number, "report": user[0].report, "emailed": user[0].emailed} for user in new_users], "role": role}
        if role == 'teacher':
            teacher_query = select(TeacherList).where(TeacherList.regUserID == id)
            teacher_result = db.execute(teacher_query)
            teacher_data = teacher_result.fetchone()
            if not teacher_data:
                return {"new_users": [], "role": role}

            set_teacher_session(request, teacher_data[0])
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            query = select(NewUsers).where(
                (cast(NewUsers.state, String) == state) &
                (cast(NewUsers.county, String) == county) &
                (cast(NewUsers.district, String) == district)
            )
            result = db.execute(query)
            new_users = result.fetchall()
            return {"new_users": [{"name": user[0].name, "email": user[0].email, "state": user[0].state, "district": user[0].district, "school": user[0].school, "phone_number": user[0].phone_number, "report": user[0].report, "emailed": user[0].emailed} for user in new_users], "role": role}
        else:
            raise HTTPException(status_code=403, detail="You don't have permission to access this page.")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")          
    finally:
        db.close()


@app.post("/profile/forgot_password/")
@limiter.limit("5/minute")
async def forgot_password(request: Request, email: str = Form(...)):
    db = SessionLocal()
    try:
        query = select(RegisteredUsers.id).where(cast(RegisteredUsers.email, String) == cast(email, String))
        result = db.execute(query)
        user = result.fetchone()
        if user:
            # Generate a secure token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            # Store the token
            reset_token = PasswordResetToken(email=email, token=token, expires_at=expires_at)
            db.add(reset_token)
            db.commit()
            # Send email with link instead of temp password
            reset_link = f"https://www.helpteachers.net/reset-password?token={token}"
            template_data = {
                'recipient_name': email,
                'message_body': (
                    f"We received a request to reset your password. "
                    f"Click the link below to reset it (expires in 1 hour):\n\n"
                    f"{reset_link}\n\n"
                    f"If you did not request this, you can ignore this email."
                )
            }
            html_message = render_email_template('static/email_template.html', template_data)
            plain_message = f"Dear {email},\n\nReset your password here: {reset_link}\n\nExpires in 1 hour."
            send_email(email, 'Password Reset Request', html_message, plain_message)
        else:
            time.sleep(1)
        return JSONResponse(content={"message": "If an account exists, a reset link will be sent to your email."})
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
    
@app.post("/profile/reset_password/")
async def reset_password(token: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    db = SessionLocal()
    try:
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")
        # Look up the token
        reset = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == 0,
            PasswordResetToken.expires_at > datetime.datetime.utcnow()
        ).first()
        if not reset:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
        # Update the password
        hashed = sha256_crypt.hash(new_password)
        db.execute(update(RegisteredUsers).where(
            cast(RegisteredUsers.email, String) == cast(reset.email, String)
        ).values(password=hashed))
        # Mark token as used
        reset.used = 1
        db.commit()
        return JSONResponse(content={"message": "Password reset successfully. You can now log in."})
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

#api that gets spotlight data based on token
@app.get("/spotlight/{token}")
async def get_spotlight_info(request: Request, token: str):
    db = SessionLocal()
    try:
        query = select(Spotlight).where(cast(Spotlight.token, String) == cast(token, String))
        result = db.execute(query)
        spotlight_info = result.fetchone()
        if spotlight_info:
            data = spotlight_info[0]
            if data.image_data:
                image_data = base64.b64encode(data.image_data).decode('utf-8')
            else:
                image_data = None
            request.session['state'] = data.state
            request.session['county'] = data.county
            if data.district:
                request.session['district'] = data.district
            if data.school:
                request.session['school'] = data.school
                request.session['teacher'] = data.name
            data_dict = {
                "state": data.state,
                "county": data.county,
                "district": data.district,
                "school": data.school,
                "name": data.name,
                "image_data": image_data
            }
            return data_dict
        else:
            raise HTTPException(status_code=404, detail="Spotlight info not found for the given token")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Internal server error")
    finally:
        db.close()

###api to get a link for the url to your page to share
@app.get("/api/teacher_url/")
async def get_teacher_url(request: Request):
    db = SessionLocal()
    try:
        state = get_index_cookie('state', request)
        county = get_index_cookie('county', request)
        district = get_index_cookie('district', request)
        school = get_index_cookie('school', request)
        name = get_index_cookie('teacher', request)
        query = select(TeacherList.url_id).where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county) &
            (cast(TeacherList.district, String) == district) &
            (cast(TeacherList.school, String) == school) &
            (cast(TeacherList.name, String) == name)
        )
        result = db.execute(query)
        token = result.fetchone()
        if not token:
            raise HTTPException(status_code=404, detail="No matching teacher found")
        url = "www.HelpTeachers.net/teacher/" + token[0]
        return {"url": url}  # Return as JSON
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")

##this api gets the token, gets the data, sets the data, then redirects
@app.get("/teacher/{url_id}")
async def get_teacher_info(url_id: str, request: Request):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(cast(TeacherList.url_id, String) == url_id)
        result = db.execute(query)
        teacher_info = result.fetchone()
        if not teacher_info:
            return RedirectResponse(url="/404")
        set_teacher_session(request, teacher_info[0])

        return RedirectResponse(url="/teacher")
    except Exception as e:
        return RedirectResponse(url="/404")

# Endpoint to  users
@app.post("/validation/delete_user/{user_email}")
async def delete_user(user_email: str, role: str = Depends(get_current_role)):
    if role == 'admin':
        db = SessionLocal()
        try:
            query = select(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
            result = db.execute(query)
            user = result.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found in new_users")
            delete_query = delete(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
            db.execute(delete_query)
            db.commit()
            return {"message": "User deleted successfully."}
        except Exception as e:
            db.rollback()
            logger.error(f"Internal Server Error: {str(e)}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()
    else:
        raise HTTPException(status_code=403, detail=f"No permission to to action.")

# Function to report a user in validation
@app.post("/validation/report_user/{user_email}")
async def report_user(user_email: str, role: str = Depends(get_current_role)):
    if role not in ('admin', 'teacher'):
        raise HTTPException(status_code=403, detail="Access denied.")
    db = SessionLocal()
    try:
        update_query = update(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String)).values(report=1)
        db.execute(update_query)
        db.commit()
        return {"message": "User reported."}
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

# Endpoint to mark that a new users has been emailed
@app.post("/validation/emailed_user/{user_email}")
async def emailed_user(user_email: str, role: str = Depends(get_current_role)):
    if role not in ('admin', 'teacher'):
        raise HTTPException(status_code=403, detail="Access denied.")
    db = SessionLocal()
    try:
        update_query = update(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String)).values(emailed=1)
        db.execute(update_query)
        db.commit()
        return {"message": "User emailed."}
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()


app.include_router(
    create_teacher_router(
        session_factory=SessionLocal,
        school_model=School,
        teacher_model=TeacherList,
        directory_response_model=TeacherDirectoryResponse,
        profile_response_model=TeacherProfileResponse,
    )
)

@app.post("/admin/generate_teacher_report/")
async def generate_teacher_report(state: str = Form(...), county: str = Form(None), district: str = Form(None), school: str = Form(None), role: str = Depends(get_current_role)):
    if role != 'admin':
        raise HTTPException(status_code=403, detail="Access denied: Only administrators can generate reports.")
    db: Session = SessionLocal()
    try:
        # Step 1: Dynamically filter TeacherList based on provided fields (excluding regUserID)
        query = select(
            TeacherList.name, TeacherList.school, TeacherList.regUserID
        ).where(cast(TeacherList.state, String) == state)

        if county:
            query = query.where(cast(TeacherList.county, String) == county)
        if district:
            query = query.where(cast(TeacherList.district, String) == district)
        if school:
            query = query.where(cast(TeacherList.school, String) == school)

        teachers = db.execute(query).fetchall()

        if not teachers:
            raise HTTPException(status_code=404, detail="No teachers found with the specified criteria.")

        # Step 2: Fetch email and phone from RegisteredUsers using regUserID
        reg_user_ids = [teacher.regUserID for teacher in teachers]
        user_query = select(
            RegisteredUsers.id,
            RegisteredUsers.email,
            RegisteredUsers.phone_number).where(RegisteredUsers.id.in_(reg_user_ids))
        users = db.execute(user_query).fetchall()

        # Step 3: Prepare data for the document
        data = ["Name\tSchool\tEmail\tPhone"]  # Tab-separated headers

        # Step 4: Map teachers to their corresponding user data (email and phone)
        user_dict = {user.id: {"email": user.email, "phone": user.phone_number} for user in users}
        for teacher in teachers:
            teacher_info = f"{teacher.name}\t{teacher.school}\t{user_dict.get(teacher.regUserID, {}).get('email', 'N/A')}\t{user_dict.get(teacher.regUserID, {}).get('phone', 'N/A')}"
            data.append(teacher_info)

        # Step 5: Prepare the file content as a string (convert list to newline-separated string)
        file_content = "\n".join(data)  # Now file_content includes both headers and teacher data

        file_name = 'teacher_report.txt'
        file_path = os.path.join('./', file_name)  # Specify the full path where the file will be saved

        with open(file_path, 'w') as temp_file:
            temp_file.write(file_content)  # Save your report data to the file

        # Step 6: Send the attachment and delete remnant on disk
        send_attachment(
            recipient_email="homeroom.heroes.main@gmail.com",
            subject="Teacher Report",
            message="Please find the attached teacher report.",
            attachment_path=file_path  # Use the specific file path
        )
        try:
            os.remove(file_path)
        except OSError:
            logger.error("Failed to delete temporary report file.")
        # Step 7: Return response
        return {"message": f"Teacher report saved and sent via email."}

    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        db.close()

# --- Modified API Endpoint for Promotional Items ---
@app.get("/{token}", response_class=HTMLResponse)
async def get_promotional_page_with_hero(request: Request, token: str):
    """
    Sets a session variable with the promo token and redirects to the homepage.
    The homepage's JavaScript will then pick up this token and display the promo hero.
    """
    lookup_token = token.lower()
    relative_image_path = PROMO_IMAGE_MAPPING.get(lookup_token)

    if not relative_image_path:
        relative_image_path = PROMO_IMAGE_MAPPING.get("default")
        if not relative_image_path:
            raise HTTPException(status_code=404, detail="Promotional image not found and no default image available in mapping.")

    full_filesystem_path = os.path.join(BASE_STATIC_DIR, relative_image_path)
    if not os.path.exists(full_filesystem_path):
        if token != "default":
            default_relative_path = PROMO_IMAGE_MAPPING.get("default")
            if default_relative_path and os.path.exists(os.path.join(BASE_STATIC_DIR, default_relative_path)):
                relative_image_path = default_relative_path
            else:
                raise HTTPException(status_code=404, detail=f"Image for token '{token}' not found and default image file is also missing.")
        else:
            raise HTTPException(status_code=404, detail="Default promotional image file not found.")

    # Store the actual static URL of the image in the session
    promo_image_url = f"/static/{relative_image_path}"
    request.session["promo_image_url"] = promo_image_url
    request.session["promo_title"] = f"Working together to serve our communities!" # Example title

    # Redirect to the homepage
    return RedirectResponse(url="/")

# --- API to get promo info (called by JavaScript) ---
@app.get("/promo/get_promo_info/")
async def get_promo_info(request: Request):
    promo_info = {
        "promo_image_url": request.session.pop("promo_image_url", None), # Pop to clear after use
        "promo_title": request.session.pop("promo_title", None),
    }
    # Clear the session variables after they are fetched
    return JSONResponse(content=promo_info)

@app.post("/forum/create_post")
@limiter.limit("5/minute")
def create_post(request: Request, title: str = Form(...), content: str = Form(...), user_id: int = Depends(get_current_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="You must be logged in to post.")
    db: Session = SessionLocal()
    # 1. Create a new ForumPost instance
    new_post = ForumPost(
        title=bleach.clean(title, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True),
        content=bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True),
        user_id=user_id
    )
    try:
        # 2. Add to session and commit
        db.add(new_post)
        db.commit()
        # 3. Refresh to get the auto-generated ID and created_at timestamp
        db.refresh(new_post)
    except Exception as e:
        db.rollback()
        print(f"Database error during post creation: {e}")
        # Return a generic error to the user
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create post due to a server error."
        )
    # 4. Return the new post data
    return new_post

@app.get("/forum/get_posts")
def get_posts():
    """
    Retrieves a list of all forum posts.

    The resulting list is ordered by creation date (newest first).
    If you implement an upvote mechanism, you can modify the order_by clause
    to use upvotes first:
    .order_by(ForumPost.upvotes.desc(), ForumPost.created_at.desc())
    """
    db: Session = SessionLocal()
   
    try:
        # Query all posts and order them by the 'created_at' column descending.
        # This returns the newest posts first, which is a good default for a feed.
        posts = db.query(ForumPost).order_by(ForumPost.created_at.desc()).all()
        return posts
    except Exception as e:
        print(f"Database error during post retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve posts due to a server error."
        )

@app.get("/forum/get_post")
def get_post(post_id: int):
    """
    Retrieves a single forum post using its unique ID.
    
    Raises HTTPException 404 if the post is not found.
    """
    db: Session = SessionLocal()
    
    try:
        # Query the database for a single post matching the provided ID
        post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
        
        # Check if the post was found
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found."
            )
            
        return post
        
    except HTTPException:
        # Re-raise the 404 exception if it was already raised
        raise
    except Exception as e:
        print(f"Database error during single post retrieval (ID: {post_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve post due to a server error."
        )

@app.post("/forum/posts/{post_id}/vote")
def handle_post_vote(post_id: int, vote_data: VoteInput, user_id: int = Depends(get_current_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="You must be logged in to post.")

    db: Session = SessionLocal()
    vote_type = vote_data.vote_type

    # 1. Input validation
    if vote_type not in (1, -1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vote type. Must be 1 (upvote) or -1 (downvote)."
        )

    # 2. Check if the post exists
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with ID {post_id} not found.")

    # 3. Check for an existing vote by this user
    existing_vote = db.query(PostVote).filter(
        PostVote.post_id == post_id,
        PostVote.user_id == user_id
    ).first()

    try:
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Case 1: Retract vote (User clicks the same button again)
                db.delete(existing_vote)
                # Subtract the existing vote type from the post's count
                post.upvote_count -= vote_type
                
            else:
                # Case 2: Change vote (e.g., upvote to downvote or vice versa)
                old_vote_value = existing_vote.vote_type
                
                # Update the vote record with the new type
                existing_vote.vote_type = vote_type
                
                # Calculate net change and update the post's cached count
                # Net Change = (New Value) - (Old Value). This handles +/-2 changes.
                net_change = vote_type - old_vote_value
                post.upvote_count += net_change

        else:
            # Case 3: New vote
            new_vote = PostVote(post_id=post_id, user_id=user_id, vote_type=vote_type)
            db.add(new_vote)
            # Add the new vote type to the post's cached count
            post.upvote_count += vote_type

        # 4. Commit all changes to PostVote and ForumPost
        db.commit()
        db.refresh(post)

    except Exception as e:
        db.rollback()
        print(f"Database error during voting operation on post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A server error prevented the vote from being recorded."
        )

    # 5. Return the updated post data
    return post

@app.post("/forum/posts/{post_id}/comment", summary="Add a new comment to a specific post")
@limiter.limit("5/minute")
def add_comment_to_post(request: Request, post_id: int, content: str = Form(...), parent_comment_id: Optional[int] = Form(None), user_id: int = Depends(get_current_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="You must be logged in to post.")
    # Assuming SessionLocal() correctly creates a DB session
    db: Session = SessionLocal() 

    # 1. Check if the parent post exists
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Post with ID {post_id} not found."
        )

    # 2. Check if a parent comment exists (if parent_comment_id is provided, for nesting)
    if parent_comment_id:
        parent_comment = db.query(ForumComment).filter(ForumComment.id == parent_comment_id).first()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Parent comment with ID {parent_comment_id} not found."
            )

    try:
        # 3. Create a new ForumComment instance
        new_comment = ForumComment(
            post_id=post_id,
            user_id=user_id,
            content=bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True),
            parent_comment_id=parent_comment_id
        )
        # 4. Add to session
        db.add(new_comment)
        
        # 5. Update the comment_count on the parent post (Denormalization)
        post.comment_count += 1 
        
        db.commit()
        db.refresh(new_comment)

    except Exception as e:
        db.rollback()
        print(f"Database error during comment creation on post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create comment due to a server error."
        )

    # 6. Return the new comment data
    # Assuming the API returns the comment object, which includes 'user_id' and 'created_at'
    return new_comment


@app.get("/forum/comments/{post_id}/")
def get_comments_for_post(post_id: int = Path(..., gt=0),) -> List[dict]:
    """
    Fetches all comments associated with a specific post, ordered by creation date (newest first).
    """
    db: Session = SessionLocal()
    
    # 1. Check if the parent post exists (Optional, but good practice)
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Post with ID {post_id} not found."
        )

    try:
        # 2. Query all comments for that post ID
        comments = db.query(ForumComment)\
                     .filter(ForumComment.post_id == post_id)\
                     .order_by(desc(ForumComment.created_at))\
                     .all()

        # 3. FIX APPLIED HERE: Convert list of SQLAlchemy model objects to list of dictionaries
        return [model_to_dict(comment) for comment in comments] 

    except Exception as e:
        print(f"Database error during comment retrieval on post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve comments due to a server error."
        )
@app.delete("/forum/post/{post_id}/delete")
def delete_post(post_id: int, role: str = Depends(get_current_role)):
    """
    Deletes a post. Only allowed for role = 'admin'.
    """
    db: Session = SessionLocal()
    try:
        if role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only administrators can delete posts."
            )

        post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        db.delete(post)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    finally:
        db.close()

@app.delete("/forum/comment/{comment_id}/delete")
def delete_comment(comment_id: int, current_user_id: int = Depends(get_current_id),role: str = Depends(get_current_role)):
    """
    Deletes a comment. Only allowed for admin OR the comment's author (not yet but can be if you uncomment below)
    """
    db: Session = SessionLocal()
    try:
        comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        is_admin = role == 'admin'
        is_author = comment.user_id == current_user_id
        if not (is_admin or is_author):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only delete your own comments or be an administrator."
            )

        post = db.query(ForumPost).filter(ForumPost.id == comment.post_id).first()
        if post and post.comment_count > 0:
            post.comment_count -= 1

        db.delete(comment)
        db.commit()
        return {"detail": f"Comment ID {comment_id} successfully deleted."}
    finally:
        db.close()

@app.patch("/forum/post/{post_id}/update")
async def update_post(post_id: int, post_data: PostUpdate, id: int = Depends(get_current_id)):
    """
    Allows the author of a post to update its title and content.
    """
    
    db: Session = SessionLocal()
    
    try:
        # 1. Fetch the existing post
        existing_post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
        
        if existing_post is None:
            raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found.")
            
        # 2. Authorization Check: Must be the original author
        # 'user' is the dictionary returned by get_current_active_user, containing the authenticated user's details
        if existing_post.user_id != id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to edit this post. You must be the author."
            )
            
        # 3. Update the post data in the SQLAlchemy model
        existing_post.title = bleach.clean(post_data.title, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
        existing_post.content = bleach.clean(post_data.content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
        
        # 4. Commit the changes to the database
        db.commit()
        
        # 5. Refresh the object to get any auto-updated fields (like a 'last_edited' timestamp if applicable)
        db.refresh(existing_post)
        
        # 6. Return the updated post
        # Note: We use response_model=PostUpdate for simplicity, 
        # but in a real app, you might use your full Post schema if it includes more fields.
        return existing_post
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback() # Rollback the transaction on any error
        # In a production environment, log the error 'e' here
        raise HTTPException(status_code=500, detail="Internal server error during post update.")
        
    finally:
        db.close()

@app.patch("/forum/comment/{comment_id}/update")
async def update_comment(comment_id: int, content: str = Form(...), user: int = Depends(get_current_id)):
    """
    Allows the author of a comment to update its content.
    """
    db: Session = SessionLocal()
    
    try:
        # 1. Fetch the existing comment
        existing_comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
        
        if existing_comment is None:
            raise HTTPException(status_code=404, detail=f"Comment with ID {comment_id} not found.")
            
        # 2. Authorization Check: Must be the original author
        if existing_comment.user_id != user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to edit this comment. You must be the author."
            )
            
        # 3. Update the content
        existing_comment.content = bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
        
        
        # 4. Commit and Refresh
        db.commit()
        db.refresh(existing_comment)
        
        # Return the updated object (FastAPI handles JSON conversion)
        return existing_comment
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error during comment update.")
        
    finally:
        db.close()


@app.post("/profile/delete/")
async def admin_delete_user_account(target_email: str = Form(...), admin_secret_input: str = Form(...),current_role: str = Depends(get_current_role)):
    """
    Allows an authenticated 'admin' user to delete *any* user account 
    by providing the target user's email and a secret key via form submission.
    Deletes the associated teacher entry and the registered user account.
    """
    db: Session = SessionLocal()
    
    # 1. ROLE CHECK: Ensure the current user is an admin
    if not current_role or current_role != 'admin':
        raise HTTPException(status_code=403, detail="Forbidden. Only administrators can delete user accounts.")

    # 2. SECRET CHECK: Ensure the provided secret matches the server configuration
    # The user-provided prompt suggests checking os.getenv("DATABASE_SERVER")
    ADMIN_SECRET = os.getenv("admin_secret")
    
    if not ADMIN_SECRET or admin_secret_input != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid administrator secret provided.")

    try:
        # 3. FIND THE TARGET USER ID
        # Select the ID of the user to be deleted based on the target email.
        user_id_query = select(RegisteredUsers.id).where(
            cast(RegisteredUsers.email, String) == cast(target_email, String)
        )
        user_id_result = db.execute(user_id_query).fetchone()

        if not user_id_result:
            raise HTTPException(status_code=404, detail=f"User account linked to '{target_email}' not found.")

        target_user_id = user_id_result[0]

        # 4. DELETE FROM teacher_list
        # Delete the entry in the teacher_list linked to this user ID (regUserID).
        delete_teacher_query = delete(TeacherList).where(
            TeacherList.regUserID == target_user_id
        )
        teacher_result = db.execute(delete_teacher_query)

        # 5. DELETE FROM registered_users
        # Delete the user account itself using the email.
        delete_user_query = delete(RegisteredUsers).where(
            cast(RegisteredUsers.email, String) == cast(target_email, String)
        )
        user_result = db.execute(delete_user_query)
        db.commit()
        return {"message": f"Successfully deleted account and associated data for target user: {target_email}."}

    except HTTPException as h:
        raise h
    except Exception as e:
        db.rollback()
        print(f"Error during administrative account deletion for {target_email}: {str(e)}")
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Internal Server Error")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
