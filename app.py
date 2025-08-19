from fastapi import FastAPI, HTTPException, Request, Form, Depends, Body, File, UploadFile, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from pydantic import BaseModel
import os, logging, smtplib, secrets, string, pyodbc, time, ssl, schedule, threading, datetime, base64, random, requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine, Column, Integer, String, func, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, cast, delete, insert, update
from datetime import date
from typing import Optional
import brevo_python
from brevo_python.rest import ApiException

app = FastAPI()
load_dotenv()
logger = logging.getLogger(__name__)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
RECAPTCHA_SECRET_KEY=os.getenv("SERVER_KEY_CAPTCHA")

# Disable documentation routes
app.openapi_url = None
app.redoc_url = None

# Determine the path to the directory
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/static", StaticFiles(directory="static"), name="static")
BASE_STATIC_DIR = "static" 

# --- Configuration for Promotional Images Mapping ---
PROMO_IMAGE_MAPPING = {
    "SeattleWolf": "images/1007TheWolf.png"
}


# Load environment variables
DATABASE_SERVER = os.getenv("DATABASE_SERVER")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_UID = os.getenv("DATABASE_UID")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")

# Construct SQLAlchemy database URL
SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc://{DATABASE_UID}:{DATABASE_PASSWORD}@{DATABASE_SERVER}:{DATABASE_PORT}/{DATABASE_NAME}?driver=ODBC+Driver+18+for+SQL+Server"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
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


# Create database tables
Base.metadata.create_all(bind=engine)


#########functions############
def get_current_id(request: Request):
    return request.session.get("user_id", None)

def get_current_role(request: Request):
    return request.session.get("user_role", None)

def get_current_email(request: Request):
    return request.session.get("user_email", None)

def get_index_cookie(index: str, request: Request):
    return request.session.get(index, None)

def store_my_cookies(request: Request, id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(TeacherList.regUserID == id)
        result = db.execute(query)
        teacher_data = result.fetchone()
        if teacher_data:
            name, state, county, district, school = teacher_data[0].name, teacher_data[0].state, teacher_data[0].county, teacher_data[0].district, teacher_data[0].school
            request.session["state"] = state
            request.session["county"] = county
            request.session["district"] = district
            request.session["school"] = school
            request.session["teacher"] = name
        else:
            raise HTTPException(status_code=404, detail="Your account does not have a database listing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
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

def send_email(recipient_email: str, subject: str, html_message: str, plain_message: str):
    """
    Sends an email with HTML content and a plain text fallback using the Brevo API.
    """
    configuration = brevo_python.Configuration()
    configuration.api_key['api-key'] = os.environ.get('BREVO_API_KEY')
    api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))
    
    send_smtp_email = brevo_python.SendSmtpEmail(
        to=[{"email": recipient_email}],
        subject=subject,
        html_content=html_message,
        text_content=plain_message,
        sender={"name": "Homeroom Heroes", "email": "homeroom.heroes.contact@gmail.com"}
    )
    
    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("Email sent successfully!")
        return api_response
    except ApiException as e:
        print(f"Exception when calling Brevo API: {e}")
        return None
        return None

def send_attachment(recipient_email: str, subject: str, message: str, attachment_path: str):
    """
    Sends an email with an attachment using the Brevo API.
    
    Args:
        recipient_email (str): The email address of the recipient.
        subject (str): The subject line of the email.
        message (str): The plain text body of the email.
        attachment_path (str): The local file path to the attachment.
    """
    # Configure API key authorization
    configuration = brevo_python.Configuration()
    configuration.api_key['api-key'] = os.environ.get('BREVO_API_KEY')

    api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))
    
    attachments = []
    if os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            encoded_content = base64.b64encode(file_data).decode('utf-8')
            
            attachments.append({
                "content": encoded_content,
                "name": os.path.basename(attachment_path)
            })
    else:
        print(f"Attachment file {attachment_path} not found. Sending email without attachment.")

    # Create the email message object
    send_smtp_email = brevo_python.SendSmtpEmail(
        to=[{"email": recipient_email}],
        subject=subject,
        html_content=f"<html><body>{message.replace('\\n', '<br>')}</body></html>",
        sender={"name": "Homeroom Heroes", "email": "homeroom.heroes.contact@gmail.com"},
        attachment=attachments
    )
    
    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("Email sent successfully with attachment!")
        return api_response
    except ApiException as e:
        print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
        return None

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
        "Best regards,\nHomeroom Heroes Team"
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
        "Best regards,\nHomeroom Heroes Team"
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
        query = select(TeacherList).order_by(func.newid()).limit(1)
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
            "Remember to share your unique page with your community."
            f"www.HelpTeachers.net/teachers/{url_id}"
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "Best regards,\nHomeroom Heroes Team"
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
            "state": random_teacher.state,
            "county": random_teacher.county,
            "district": random_teacher.district,
        }
        store_spotlight(teacher_info, "district")
    else:
        print("No random teacher found.")

def first_of_month_job():
    if date.today().day == 1:
        random_teacher = fetch_random_teacher()
        if random_teacher:
            teacher_info = {
                "state": random_teacher.state,
                "county": random_teacher.county
            }
            store_spotlight(teacher_info, "county")
        else:
            print("No random teacher found.")
    else:
        print('Not the first.')

def schedule_jobs():
    schedule.every().tuesday.at("13:50").do(tuesday_job)
    schedule.every().thursday.at("06:00").do(thursday_job)
    schedule.every().day.at("13:50").do(daily_job)
    schedule.every().monday.at("06:00").do(monday_job)
    schedule.every().day.at("06:00").do(first_of_month_job)

    # Run the schedule in a separate thread
    while True:
        schedule.run_pending()
        time.sleep(1)

def verify_recaptcha(recaptcha_response: str):
    """Verifies the reCAPTCHA response with Google's servers."""
    url = "https://www.google.com/recaptcha/api/siteverify"
    params = {"secret": RECAPTCHA_SECRET_KEY, "response": recaptcha_response}
    response = requests.post(url, params=params)
    data = response.json()
    return data["success"]

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
            "www.HelpTeachers.net"
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
        "Best regards,\nHomeroom Heroes Team"
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
        "Best regards,\nHomeroom Heroes Team"
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

# Start scheduling the jobs
schedule_thread = threading.Thread(target=schedule_jobs)
schedule_thread.start()



#######apis#######
###api used to register a new user (and only a new user) into the new_user list
@app.post("/register/")
async def register_user(name: str = Form(...), email: str = Form(...), phone_number: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), state: str = Form(...),county: str = Form(...),district: str = Form(...), school: str = Form(...), recaptcha_response: str = Form(...)):
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
        return {"message": "Registration unsuccessful", "error": str(e)}


###api used to create cookie based session via authentication with registered_user table
@app.post("/login/")
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
                message = "Invalid password."
        else:
            message = "Invalid email."
        return JSONResponse(content={"message": message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

##end cookie session
@app.post("/logout/")
async def logout_user(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
        del request.session["user_role"]
        del request.session["user_email"]
    return RedirectResponse(url="/", status_code=303)

# Endpoint to move a user from new_users to registered_users and delete item in new_users
@app.post("/validate_user/{user_email}")
async def move_user(user_email: str):
    db = SessionLocal()
    try:
        query = select(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
        result = db.execute(query)
        user = result.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in new_users")
        query = insert(RegisteredUsers).values(email=user[0].email, password=user[0].password, role=user[0].role, phone_number = user[0].phone_number)
        db.execute(query)
        delete_query = delete(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
        db.execute(delete_query)
        db.commit()
        send_validation_email(user[0].email)        
        return {"message": "User validated."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

##this api allows a logged in user to create an item in the table teacher_list in the hithero database if they have not created a user already
@app.post("/create_teacher_profile/")
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
                random_number = random.randint(1, 9999)
                auto_url_id = f"{first_part_email}{random_number}"
                while db.execute(select(TeacherList).where(cast(TeacherList.url_id, String) == cast(auto_url_id, String))).first():
                    random_number = random.randint(1, 9999)
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

##api gets a random teacher from the list teacher_list in the hithero data base
@app.get("/random_teacher/")
async def get_random_teacher(request: Request):
    db = SessionLocal()
    try:
        random_teacher = fetch_random_teacher()
        if random_teacher:
            if random_teacher.image_data:
                image_data = base64.b64encode(random_teacher.image_data).decode('utf-8')
            else:
                image_data = None
            data = {
                "name": random_teacher.name,
                "state": random_teacher.state,
                "county": random_teacher.county,
                "district": random_teacher.district,
                "school": random_teacher.school,
                "image_data": image_data
            }
            request.session["state"] = data["state"]
            request.session["county"] = data["county"]
            request.session["district"] = data["district"]
            request.session["school"] = data["school"]
            request.session["teacher"] = data["name"]
            return data
        else:
            raise HTTPException(status_code=404, detail="No teachers found in the database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()


###api gets the current session info of the logged in user
@app.get("/profile/")
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
@app.post('/contact_us/')
async def contact_us(name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...), recaptcha_response: str = Form(...)):

    # reCAPTCHA verification
    is_valid = verify_recaptcha(recaptcha_response)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")

    # Define the data to populate the template
    template_data = {
        'recipient_name': 'Homeroom Heroes Team',
        'message_body': f"Message from {name} ({email}):\n\n{message}"
    }

    # 1. Generate the HTML message from the template
    # The path is correctly specified relative to the project root
    html_message = render_email_template('static/email_template.html', template_data)

    # 2. Create a plain text fallback version
    plain_message = (
        f"Subject: {subject}\n"
        f"Message from {name} ({email}):\n\n"
        f"{message}"
    )

    recipient_email = 'Homeroom.heroes.contact@gmail.com'
    try:
        send_email(recipient_email, subject, html_message, plain_message)
        return {"message": "Email sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

#homepage get
@app.get("/")
def read_root():
    return RedirectResponse("/pages/homepage.html")

# Custom 404 error handler
@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    with open(os.path.join("pages/", "404.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=404)

# Custom 403 error handler
@app.exception_handler(403)
async def forbidden(request: Request, exc: HTTPException):
    with open(os.path.join("pages/", "403.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=403)

###api gets a teacher data from teacher_list table
@app.get("/get_teacher_info/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

##api that updates about me info
@app.post("/update_info/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

##api that updates school
@app.post("/update_teacher_school/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

##api that updates name
@app.post("/update_teacher_name/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

##api to update wishlist
@app.post("/update_wishlist/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()


#api that update the url of a teachers page
@app.post("/update_url_id/")
async def update_url_id(request: Request, url_id: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

    
###api used to update the logged in users teacher page image
@app.post("/update_teacher_image/")
async def edit_teacher_image(request: Request, role: str = Depends(get_current_role), image: UploadFile = Form(...)):
    db: Session = SessionLocal()
    try:
        if image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds the allowed limit")
        if role:
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie('school', request)
            name = get_index_cookie('teacher', request)
            new_image_data = image.file.read()
            update_query = update(TeacherList).values(image_data=new_image_data).where(
                (cast(TeacherList.state, String) == state) &
                (cast(TeacherList.county, String) == county) &
                (cast(TeacherList.district, String) == district) &
                (cast(TeacherList.school, String) == school) &
                (cast(TeacherList.name, String) == name)
            )
            db.execute(update_query)
            db.commit()
            return {"message": "Information updated."}
        else:
            return {"message": "Permission denied."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()


##api gets your page based on the id in reg_users and and regUserID in teacher_list
@app.get("/myinfo/")
async def get_myinfo(request: Request, id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(TeacherList.regUserID == id)
        result = db.execute(query)
        teacher_data = result.fetchone()
        if teacher_data:
            state = teacher_data[0].state
            county = teacher_data[0].county
            district = teacher_data[0].district
            school = teacher_data[0].school
            name = teacher_data[0].name
            request.session["state"] = state
            request.session["county"] = county
            request.session["district"] = district
            request.session["school"] = school
            request.session["teacher"] = name
            return {"state": state, "county": county, "district": district, "school": school, "teacher": name}
        else:
            return {"message": "Your account does not have a database listing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()


##api lets the logged in user update their password
@app.post("/update_password/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()


#api to check if a user has edit acces to teacher page
@app.get("/check_access_teacher/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()


#gets a list of unverified users to validate based on the role of the user
@app.get("/validation_list/")
async def validation_page(request: Request, role: str = Depends(get_current_role), id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        if role == "admin":
            query = select(NewUsers)
            result = db.execute(query)
            new_users = result.fetchall()
            return {"new_users": [{"name": user[0].name, "email": user[0].email, "state": user[0].state, "district": user[0].district, "school": user[0].school, "phone_number": user[0].phone_number, "report": user[0].report, "emailed": user[0].emailed} for user in new_users], "role": role}
        if role == 'teacher':
            store_my_cookies(request, id)
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")          
    finally:
        db.close()


#api gets a list of states from statecoutny table
@app.get("/get_states/")
async def get_states():
    db = SessionLocal()
    try:
        states = db.query(School.state).distinct().all()
        return sorted([state[0] for state in states])
    finally:
        db.close()

#api gets the names of the counties in the desired state
@app.get("/get_counties/{state}")
async def get_counties(state: str):
    db = SessionLocal()
    try:
        query = select(School.county).distinct().where(School.state == state)
        result = db.execute(query)
        counties = result.fetchall()
        if counties:
            county_names = sorted([county[0] for county in counties])
            return county_names
        else:
            return {"message": f"No counties found for state: {state}"}
    finally:
        db.close()

#api gets the names of the school districts in the desired county and state
@app.get("/get_districts/{state}/{county}")
async def get_districts(state: str, county: str):
    db = SessionLocal()
    try:
        query = select(School.district).distinct().where((School.state == state) & (School.county == county))
        result = db.execute(query)
        districts = result.fetchall()
        if districts:
            district_names = sorted([district[0] for district in districts])
            return district_names
        else:
            return {"message": f"No districts found for state: {state} and county: {county}"}
    finally:
        db.close()

#api gets the names of the school in the desired district, coutny, and state
@app.get("/get_schools/{state}/{county}/{district}")
async def get_schools(state: str, county: str, district: str):
    db = SessionLocal()
    try:
        query = select(School.school_name).distinct().where((School.state == state) & (School.county == county) & (School.district == district))
        result = db.execute(query)
        schools = result.fetchall()
        if schools:
            school_names = sorted([school[0] for school in schools])
            return school_names
        else:
            return {"message": f"No schools found for state: {state}, county: {county}, and district: {district}"}
    finally:
        db.close()

# api for forgotten password reset, currently does not do anything exceptional
@app.post("/forgot_password/")
async def forgot_password(email: str = Form(...)):
    db = SessionLocal()
    try:
        query = select(RegisteredUsers.id).where(cast(RegisteredUsers.email, String) == cast(email, String))
        result = db.execute(query)
        user = result.fetchone()
        if user:
            recipient_email = email
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(10))
            
            # --- Prepare data for the HTML template ---
            template_data = {
                'recipient_name': email, # Using email as the name for the template
                'message_body': (
                    f"We have received a request for a password reset for your account. "
                    f"Here is your new temporary password: <strong>{temp_password}</strong>. " # Bold the temporary password
                    f"Please use this password the next time you login and update it immediately.\n\n"
                    f"If you did not request this password reset or have any concerns, "
                    f"please contact our support team."
                )
            }

            # Generate the HTML message from the template file
            html_message = render_email_template('static/email_template.html', template_data)

            # Create the plain text fallback message
            plain_message = (
                f"Dear {email},\n\n"
                f"We have received a request for a password reset for your account. "
                f"Here is your new temporary password: {temp_password}. "
                f"Please use this password the next time you login and update it immediately.\n\n"
                f"If you did not request this password reset or have any concerns, "
                f"please contact our support team.\n\n"
                f"Best regards,\nHomeroom Heroes Team"
            )

            # Send the email using the updated send_email function
            send_email(recipient_email, 'Forgot Password', html_message, plain_message)
            
            # Update the user's temporary password in the database
            update_temp_password(db, recipient_email, temp_password)
        else:
            # Add a small delay for security reasons even if the email doesn't exist
            time.sleep(1) 
        message = "If an account exists, instructions for password reset will be sent to your email. Check your spam folder."
        return JSONResponse(content={"message": message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        db.close()

###api to get a link for the url to your page to share
@app.get("/teacher_url/")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

##this api gets the token, gets the data, sets the data, then redirects
@app.get("/teacher/{url_id}")
async def get_teacher_info(url_id: str, request: Request):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(cast(TeacherList.url_id, String) == url_id)
        result = db.execute(query)
        teacher_info = result.fetchone()
        if not teacher_info:
            return RedirectResponse(url="/pages/404.html")
        request.session['state'] = teacher_info[0].state
        request.session['county'] = teacher_info[0].county
        request.session['district'] = teacher_info[0].district
        request.session['school'] = teacher_info[0].school
        request.session['teacher'] = teacher_info[0].name

        return RedirectResponse(url="/pages/teacher.html")
    except Exception as e:
        return RedirectResponse(url="/pages/404.html")

# Endpoint to move a user from new_users
@app.post("/delete_user/{user_email}")
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
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        finally:
            db.close()
    else:
        raise HTTPException(status_code=500, detail=f"No permission to to action.")

# Function to report a user in validation
@app.post("/report_user/{user_email}")
async def report_user(user_email: str):
    db = SessionLocal()
    try:
        update_query = update(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String)).values(report=1)
        db.execute(update_query)
        db.commit()
        return {"message": "User reported."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

# Endpoint to mark that a new users has been emailed
@app.post("/emailed_user/{user_email}")
async def emailed_user(user_email: str):
    db = SessionLocal()
    try:
        update_query = update(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String)).values(emailed=1)
        db.execute(update_query)
        db.commit()
        return {"message": "User emailed."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()


#api gets a list of states from statecoutny table
@app.get("/index_states/")
async def index_states():
    db = SessionLocal()
    try:
        states = db.query(cast(TeacherList.state, String)).distinct().all()
        return sorted([state[0] for state in states])
    finally:
        db.close()

#api gets the names of the counties in the desired state
@app.get("/index_counties/{state}")
async def index_counties(state: str):
    db = SessionLocal()
    try:
        query = select(cast(TeacherList.county, String)).distinct().where(cast(TeacherList.state, String) == state)
        result = db.execute(query)
        counties = result.fetchall()
        if counties:
            county_names = sorted([county[0] for county in counties])
            return county_names
        else:
            return {"message": f"No counties found for state: {state}"}
    finally:
        db.close()

#api gets the names of the school districts in the desired county and state
@app.get("/index_districts/{state}/{county}")
async def index_districts(state: str, county: str):
    db = SessionLocal()
    try:
        query = select(cast(TeacherList.district, String)).distinct().where((cast(TeacherList.state, String) == state) & (cast(TeacherList.county, String) == county))
        result = db.execute(query)
        districts = result.fetchall()
        if districts:
            district_names = sorted([district[0] for district in districts])
            return district_names
        else:
            return {"message": f"No districts found for state: {state} and county: {county}"}
    finally:
        db.close()

#api gets the names of the school in the desired district, coutny, and state
@app.get("/index_schools/{state}/{county}/{district}")
async def index_schools(state: str, county: str, district: str):
    db = SessionLocal()
    try:
        query = select(cast(TeacherList.school, String)).distinct().where((cast(TeacherList.state, String) == state) & (cast(TeacherList.county, String) == county) & (cast(TeacherList.district, String) == district))       
        result = db.execute(query)
        schools = result.fetchall()
        if schools:
            school_names = sorted([school[0] for school in schools])
            return school_names
        else:
            return {"message": f"No schools found for state: {state}, county: {county}, and district: {district}"}
    finally:
        db.close()

###api gets the teachers and their url_id for the index
@app.post("/index_teachers/")
async def index_teachers(state: str = Form(...),county: str = Form(None),district: str = Form(None),school: str = Form(None)):
    db: Session = SessionLocal()
    try:
        query = select(TeacherList.name, TeacherList.url_id).where(
            (cast(TeacherList.state, String) == state)
        )

        if county:
            query = query.where(cast(TeacherList.county, String) == county)
        if district:
            query = query.where(cast(TeacherList.district, String) == district)
        if school:
            query = query.where(cast(TeacherList.school, String) == school)

        result = db.execute(query)
        teachers = result.fetchall()

        if teachers:
            return [{"name": teacher.name, "url_id": teacher.url_id} for teacher in teachers]
        else:
            raise HTTPException(
                status_code=404,
                detail="No teachers found with the given criteria."
            )
    finally:
        db.close()

@app.post("/generate_teacher_report/")
async def generate_teacher_report(state: str = Form(...), county: str = Form(None), district: str = Form(None), school: str = Form(None)):
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

        # Step 6: Send the attachment
        send_attachment(
            recipient_email="homeroom.heroes.main@gmail.com",
            subject="Teacher Report",
            message="Please find the attached teacher report.",
            attachment_path=file_path  # Use the specific file path
        )

        # Step 7: Return response
        return {"message": f"Teacher report saved and sent via email. The report is located at {file_path}"}

    except Exception as e:
        raise e

    finally:
        db.close()

# --- Modified API Endpoint for Promotional Items ---
@app.get("/promo/{token}", response_class=HTMLResponse)
async def get_promotional_page_with_hero(request: Request, token: str):
    """
    Sets a session variable with the promo token and redirects to the homepage.
    The homepage's JavaScript will then pick up this token and display the promo hero.
    """
    relative_image_path = PROMO_IMAGE_MAPPING.get(token)

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
    return RedirectResponse(url="/pages/homepage.html")

# --- API to get promo info (called by JavaScript) ---
@app.get("/get_promo_info/")
async def get_promo_info(request: Request):
    promo_info = {
        "promo_image_url": request.session.pop("promo_image_url", None), # Pop to clear after use
        "promo_title": request.session.pop("promo_title", None),
    }
    # Clear the session variables after they are fetched
    return JSONResponse(content=promo_info)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
