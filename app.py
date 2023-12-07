from fastapi import FastAPI, HTTPException, Request, Form, Depends, Body, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
import pyodbc
import string
import secrets
import smtplib
import logging
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from email.mime.text import MIMEText

app = FastAPI()
logger = logging.getLogger(__name__)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# Determine the path to the directory
pages_directory = os.path.join(os.path.dirname(__file__), "pages")
app.mount("/pages", StaticFiles(directory=pages_directory), name="pages")
static_directory = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_directory), name="static")
load_dotenv()

# Define your AAD ODBC connection string
connection_string = os.getenv("DATABASE_CONNECTION_STRING")

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

def get_index_cookie(index: str, request: Request):
    return request.session.get(index, None)



#######apis#######
###api used to register a new user (and only a new user) into the new_user list
@app.post("/register/")
async def register_user(name: str = Form(...), email: str = Form(...), phone_number: str = Form(...), role: str = Form(...)):
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM registered_users WHERE CAST(email AS nvarchar) = ?", email)
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    cursor.execute("SELECT id FROM new_users WHERE CAST(email AS nvarchar) = ?", email)
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email is already in the registration queue")
    insert_query = "INSERT INTO new_users (name, email, phone_number, role) VALUES (?, CAST(? AS NVARCHAR), ?, ?)"
    cursor.execute(insert_query, (name, email, phone_number, role))
    connection.commit()
    cursor.close()
    return {"message": "User registered successfully"}

###api used to create cookie based session via authentication with registered_user table
@app.post("/login/")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    cursor = connection.cursor()
    cursor.execute("SELECT id, role FROM registered_users WHERE CAST(email AS NVARCHAR) = ? AND CAST(password AS NVARCHAR) = ?", (email, password))
    user = cursor.fetchone()
    cursor.close()
    if user:
        message = "Login successful as " + user.role
        request.session["user_name"] = email
        request.session["user_role"] = user.role
        request.session["user_id"] = user.id
        return JSONResponse(content={"message": message})
    else:
        message = "Invalid email or password"
        return JSONResponse(content={"message": message}, status_code=400)

##end cookie session
@app.post("/logout/")
async def logout_user(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
        del request.session["user_role"]
        del request.session["user_name"]
    return RedirectResponse(url="/", status_code=303)

# Endpoint to move a user from new_users to registered_users and delete item in new_users
@app.post("/move_user/{user_email}")
async def move_user(user_email: str):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM new_users WHERE CAST(email AS NVARCHAR) = ?", user_email)
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in new_users")
    password_characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(password_characters) for _ in range(10))
    cursor.execute("INSERT INTO registered_users (email, password, role) "
                   "VALUES (?, ?, ?)",
                   (user.email, password, user.role))
    connection.commit()
    cursor.execute("DELETE FROM new_users WHERE CAST(email AS NVARCHAR) = ?", user_email)
    connection.commit()
    cursor.close()
    return {"message": "User moved from new_users to registered_users"}

##this api updates the registered_users blank fields. School can be none because superintendents dont have a specific school
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

##this api allows a logged in user to create an item in the table teacher_list in the hithero database. 
##if the user is a teacher, the regUser value is set the the logged in users ID from registered_users
@app.post("/create_teacher_item/")
async def create_teacher_item(name: str, state: str, county: str, district: str, school: str, role: str = Depends(get_current_role), email: str = Depends(get_current_user)):
    if role:
        cursor = connection.cursor()
        insert_query = "INSERT INTO teacher_list (name, state, county, district, school) " \
                    "VALUES (?, ?, ?, ?, ?, ?)"
        cursor.execute(insert_query, (first_name, last_name, state, county, district, school))
        if role == 'teacher':
            cursor.execute("SELECT MAX(id) FROM teacher_list")
            max_teacher_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM registered_users WHERE CAST(email AS NVARCHAR) = ?", email)
            reg_user_id = cursor.fetchone()

            if max_teacher_id and reg_user_id:
                update_query = "UPDATE teacher_list SET regUserID = ? WHERE id = ?"
                cursor.execute(update_query, (reg_user_id[0], max_teacher_id))
        connection.commit()
        cursor.close()
        return {"message": f"Teacher created successfully"}
    else:
        raise HTTPException(status_code=404, detail="No user logged in.")

##api gets a random teacher from the list teacher_list in the hithero data base
@app.get("/random_teacher/")
async def get_random_teacher(request: Request):
    cursor = connection.cursor()
    cursor.execute("SELECT TOP 1 name, state, county, district, school FROM teacher_list ORDER BY NEWID()")
    random_teacher = cursor.fetchone()
    cursor.close()
    if random_teacher:
        data = {
            "name": random_teacher.name,
            "state": random_teacher.state,
            "county": random_teacher.county,
            "district": random_teacher.district,
            "school": random_teacher.school
        }
        request.session["state"] = data["state"]
        request.session["county"] = data["county"]
        request.session["district"] = data["district"]
        request.session["school"] = data["school"]
        request.session["name"] = data["name"]
        return data
    else:
        raise HTTPException(status_code=404, detail="No teachers found in the database")

###api gets the current session info of the logged in user
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

##api used to send contact us email from /contact.html
@app.post('/contact_us/')
def contact_us(name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...)):
    sender_email = 'hometown.heroes.main@gmail.com'
    password_data = get_email_password()
    recipient_email = 'hometown.heroes.contactUs@gmail.com'

    subject = f"Contact Us Form Submission: {subject}"
    email_message = f"Name: {name}\nEmail: {email}\nMessage: {message}"

    msg = MIMEText(email_message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
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
    with open(os.path.join(pages_directory, "404.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=404)

# Custom 403 error handler
@app.exception_handler(403)
async def forbidden(request: Request, exc: HTTPException):
    with open(os.path.join(pages_directory, "403.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=403)

##api is used to store the selected name as a cookie named index
##index is: state, county, district, school, teacher
@app.post("/store_cookie/{index}/{name}")
async def store_cookie(name: str, index: str, request: Request):
    try:
        request.session[index] = name
        return {"message": "String saved as a session cookie"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

##api gets the wanted cookie
@app.get("/get_cookie/{index}")
async def get_cookie(index: str, request: Request):
    try:
        cookie = {
            'cookie': get_index_cookie(index, request)
        }
        return JSONResponse(content=cookie)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

###api gets a list from the database table teacher_list
@app.get("/get_index_list/{index}")
async def get_index_list(index: str, request: Request):
    try:
        cursor = connection.cursor()
        if index == "state":
            state = get_index_cookie(index, request)
            cursor.execute("SELECT county FROM teacher_list WHERE CAST(state AS nvarchar) = ?", state)
        elif index == "county":
            county = get_index_cookie(index, request)
            cursor.execute("SELECT district FROM teacher_list WHERE CAST(county AS nvarchar) = ?", county)
        elif index == "district":
            district = get_index_cookie(index, request)
            cursor.execute("SELECT school FROM teacher_list WHERE CAST(district AS nvarchar) = ?", district)
        elif index == "school":
            school = get_index_cookie(index, request)
            cursor.execute("SELECT name FROM teacher_list WHERE CAST(school AS nvarchar) = ?", school)
        rows = cursor.fetchall()
        unique = set(row[0] for row in rows)
        result_list = list(unique)
        return result_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

###api gets a teacher data from teacher_list table
@app.get("/get_teacher_info/")
async def get_teacher_info(request: Request):
        try:
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie('school', request)
            name = get_index_cookie('teacher', request)
            cursor = connection.cursor()
            cursor.execute("SELECT wishlist_url, about_me FROM teacher_list WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND  CAST(district AS nvarchar) = ? AND CAST(school AS nvarchar) = ? AND CAST(name AS nvarchar) = ?", state, county, district, school, name)
            teacher_info = cursor.fetchone()
            if teacher_info:
                data = {
                    "state": state,
                    "county": county,
                    "district": district,
                    "school": school,
                    "teacher": name,
                    "wishlist_url": teacher_info[0],
                    "about_me": teacher_info[1],
                }
                return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

###api used to update the logged in users teacher page, currently only admins can edit any page
@app.post("/update_teacher_info/")
async def edit_teacher_info(request: Request, wishlist: str = Form(...), aboutMe: str = Form(...), role: str = Depends(get_current_role)):
    if role == 'admin':
        state = get_index_cookie('state', request)
        county = get_index_cookie('county', request)
        district = get_index_cookie('district', request)
        school = get_index_cookie('school', request)
        name = get_index_cookie('teacher', request)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE teacher_list SET wishlist_url = ?, about_me = ? WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND CAST(district AS nvarchar) = ? AND CAST(school AS nvarchar) = ? AND CAST(name AS nvarchar) = ?",
            wishlist, aboutMe, state, county, district, school, name
        )
        connection.commit()

        return JSONResponse(content={"success": True}, status_code=200)
    else:
        # User is not an admin, return an error
        raise HTTPException(status_code=403, detail="Permission denied. Only admins can edit teacher information.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
