from fastapi import FastAPI, HTTPException, Request, Form, Depends, Body, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
import pyodbc
import string
import secrets
import smtplib
import logging
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from email.mime.text import MIMEText

app = FastAPI()

logger = logging.getLogger(__name__)

# Configure the session middleware
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Determine the path to the directory containing the static pages
pages_directory = os.path.join(os.path.dirname(__file__), "pages")

# Mount the 'pages' directory to be served at '/pages'
app.mount("/pages", StaticFiles(directory=pages_directory), name="pages")

# Determine the path to the directory containing the static pages
static_directory = os.path.join(os.path.dirname(__file__), "static")

# Mount the 'pages' directory to be served at '/pages'
app.mount("/static", StaticFiles(directory=static_directory), name="static")

# Define your AAD ODBC connection string
connection_string = (
    'Driver={ODBC Driver 18 for SQL Server};'
    'Server=tcp:hithero.database.windows.net,1433;'
    'Database=hithero_login;'
    'Uid=hithero_admin;'
    'Pwd=MedL&ke15;'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

try:
    # Define the ODBC connection
    connection = pyodbc.connect(connection_string)
except pyodbc.Error as e:
    raise Exception(f"Error connecting to the database: {str(e)}")


#########functions############
def get_current_id(request: Request):
    return request.session.get("user_id", None)

def get_current_role(request: Request):
    return request.session.get("user_role", None)

def get_current_user(request: Request):
    return request.session.get("user_name", None)

def get_email_password():
    connection = pyodbc.connect(connection_string)
    cursor = connection.cursor()
    cursor.execute("SELECT password FROM hitheroEmail WHERE CAST(email AS NVARCHAR) = ?", 'hometown.heroes.main@gmail.com')
    data = cursor.fetchone()
    password = data[0]
    return password

#######apis#######
@app.post("/register/")
async def register_user(first_name: str = Form(...), last_name: str = Form(...), email: str = Form(...), phone_number: str = Form(...), role: str = Form(...)):
    # Connect to the database
    cursor = connection.cursor()

    # Check if a user with the provided email already exists in registered_users
    print("Checking for user in registered users.")
    cursor.execute("SELECT id FROM registered_users WHERE CAST(email AS nvarchar) = ?", email)
    existing_user = cursor.fetchone()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Check if a user with the provided email already exists in new_users
    print("Checking in new users.")
    cursor.execute("SELECT id FROM new_users WHERE CAST(email AS nvarchar) = ?", email)
    existing_user = cursor.fetchone()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email is already in the registration queue")

    # Insert the new user into the "new_users" table
    insert_query = "INSERT INTO new_users (first_name, last_name, email, phone_number, role) VALUES (?, ?, CAST(? AS NVARCHAR), ?, ?)"
    cursor.execute(insert_query, (first_name, last_name, email, phone_number, role))
    connection.commit()

    cursor.close()
    return {"message": "User registered successfully"}

@app.post("/login/")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    # Connect to the database (You should replace this with your actual database connection logic)
    cursor = connection.cursor()

    # Check if a user with the provided email and password exists in registered_users
    cursor.execute("SELECT id, role FROM registered_users WHERE CAST(email AS NVARCHAR) = ? AND CAST(password AS NVARCHAR) = ?", (email, password))
    user = cursor.fetchone()

    cursor.close()  # Close the cursor after the query is executed

    if user:
        message = "Login successful as " + user.role

         # Set user session data
        request.session["user_name"] = email
        request.session["user_role"] = user.role
        request.session["user_id"] = user.id

        return JSONResponse(content={"message": message})
    else:
        message = "Invalid email or password"
        return JSONResponse(content={"message": message}, status_code=400)

@app.post("/logout/")
async def logout_user(request: Request):
    # Clear user session data to log out
    if "user_id" in request.session:
        del request.session["user_id"]
        del request.session["user_role"]
        del request.session["user_name"]
    # Redirect to the homepage or another page after logout
    return RedirectResponse(url="/", status_code=303)

# Endpoint to move a user from new_users to registered_users
@app.post("/move_user/{user_email}")
async def move_user(user_email: str):
    cursor = connection.cursor()

    # Check if the user exists in new_users
    cursor.execute("SELECT * FROM new_users WHERE CAST(email AS NVARCHAR) = ?", user_email)
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found in new_users")

    # Generate a random 10-character password
    password_characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(password_characters) for _ in range(10))

    # Move the user to registered_users
    cursor.execute("INSERT INTO registered_users (email, password, role) "
                   "VALUES (?, ?, ?)",
                   (user.email, password, user.role))
    connection.commit()

    # Remove the user from new_users
    cursor.execute("DELETE FROM new_users WHERE CAST(email AS NVARCHAR) = ?", user_email)
    connection.commit()

    cursor.close()

    return {"message": "User moved from new_users to registered_users"}

@app.put("/update/")
async def update_user_fields(email: str, state: str, county: str, district: str, school: str = None):
    query = (
        "UPDATE registered_users SET state = ?, county = ?, district = ?, school = ? "
        "WHERE CAST(email AS NVARCHAR) = ?"
    )
    values = (state, county, district, school, email)

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
            connection.commit()
        return {"message": f"User with email {email} fields updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_teacher_item/")
async def create_teacher_item(first_name: str, last_name: str, state: str, county: str, district: str, school: str, role: str = Depends(get_current_role), email: str = Depends(get_current_user)):
    if role:
        # Connect to the database
        cursor = connection.cursor()

        # Insert the new item into the "teacher_list" table
        insert_query = "INSERT INTO teacher_list (first_name, last_name, state, county, district, school) " \
                    "VALUES (?, ?, ?, ?, ?, ?)"
        cursor.execute(insert_query, (first_name, last_name, state, county, district, school))

        # Link registered user to the teacher with the highest ID
        if role == 'teacher':
            # Get the maximum ID from the teacher_list table
            cursor.execute("SELECT MAX(id) FROM teacher_list")
            max_teacher_id = cursor.fetchone()[0]  # Get the maximum ID

            # Next, get the ID of the registered user based on their email
            cursor.execute("SELECT id FROM registered_users WHERE CAST(email AS NVARCHAR) = ?", email)
            reg_user_id = cursor.fetchone()

            if max_teacher_id and reg_user_id:
                # Link the registered user to the teacher with the highest ID
                update_query = "UPDATE teacher_list SET regUserID = ? WHERE id = ?"
                cursor.execute(update_query, (reg_user_id[0], max_teacher_id))

        connection.commit()

        cursor.close()
        return {"message": f"Teacher created successfully"}
    else:
        raise HTTPException(status_code=404, detail="No user logged in.")

@app.get("/random_teacher/")
async def get_random_teacher():
    # Connect to the database
    cursor = connection.cursor()

    # Query the database to retrieve a random teacher
    cursor.execute("SELECT TOP 1 first_name, last_name, state, county, district, school FROM teacher_list ORDER BY NEWID()")
    random_teacher = cursor.fetchone()

    cursor.close()

    if random_teacher:
        data = {
            "first_name": random_teacher.first_name,
            "last_name": random_teacher.last_name,
            "state": random_teacher.state,
            "county": random_teacher.county,
            "district": random_teacher.district,
            "school": random_teacher.school
        }
        
        return data

    else:
        raise HTTPException(status_code=404, detail="No teachers found in the database")

@app.get("/profile/")
async def get_user_profile(username: str = Depends(get_current_user), role: str = Depends(get_current_role), id: str = Depends(get_current_id)):
    if username:
        user_info = {
            "user_id": username,
            "user_role": role,
            "user_name": id
        }
        return JSONResponse(content=user_info)
    else:
        raise HTTPException(status_code=404, detail="No user logged in.")

@app.post('/contact_us/')
def contact_us(name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...)):
    sender_email = 'hometown.heroes.main@gmail.com'  # Your email address
    password_data = get_email_password()  # Your email password
    recipient_email = 'hometown.heroes.contactUs@gmail.com'  # Your email address

    subject = f"Contact Us Form Submission: {subject}"
    email_message = f"Name: {name}\nEmail: {email}\nMessage: {message}"

    msg = MIMEText(email_message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Use the SMTP server of your email provider
        server.starttls()
        server.login(sender_email, password_data)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        message = 'Email sent successfully!'
        return JSONResponse(content={"message": message})
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {str(e)}")
        message = "Error: Authentication failed. Check your email credentials."
        return JSONResponse(content={"message": message}, status_code=400)
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        message = f"Error: {str(e)}"
        return JSONResponse(content={"message": message}, status_code=400)

#homepage get
@app.get("/")
def read_root():
    return RedirectResponse("/pages/homepage.html")

# Custom 404 error handler
@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    # Load the custom 404 HTML page
    with open(os.path.join(pages_directory, "404.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=404)

# Custom 403 error handler
@app.exception_handler(403)
async def forbidden(request: Request, exc: HTTPException):
    # Load the content of the "403.html" file
    with open(os.path.join(pages_directory, "403.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=403)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
