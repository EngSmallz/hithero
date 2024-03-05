from fastapi import FastAPI, HTTPException, Request, Form, Depends, Body, APIRouter, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
import os, logging, smtplib, secrets, string, pyodbc, time, ssl
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from passlib.hash import sha256_crypt


app = FastAPI()
load_dotenv()
logger = logging.getLogger(__name__)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# Determine the path to the directory
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define your AAD ODBC connection string
connection_string = (f'Driver={os.getenv("DATABASE_DRIVER")};Server={os.getenv("DATABASE_SERVER")};Database={os.getenv("DATABASE_NAME")};Uid={os.getenv("DATABASE_UID")};Pwd={os.getenv("DATABASE_PASSWORD")};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;ConnectRetryCount=255;')

# Define the ODBC connection
try:
    connection = pyodbc.connect(connection_string)
except pyodbc.Error as e:
    raise Exception(f"Error connecting to the database: {str(e)}")


#########functions############
def connect_to_db():
    try:
        connection = pyodbc.connect(connection_string)
    except pyodbc.Error as e:
        raise Exception(f"Error connecting to the database: {str(e)}")

def get_current_id(request: Request):
    return request.session.get("user_id", None)

def get_current_role(request: Request):
    return request.session.get("user_role", None)

def get_current_email(request: Request):
    return request.session.get("user_email", None)

def get_email_password(email: str):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM hitheroEmail WHERE CAST(email AS NVARCHAR) = ?", email)
        data = cursor.fetchone()
        password = data[0]
        return password
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

def get_index_cookie(index: str, request: Request):
    return request.session.get(index, None)

def decode_image(hex_string):
    try:
        # Convert hex string to bytes
        image_bytes = bytes.fromhex(hex_string)
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def store_my_cookies(request: Request, id: int = Depends(get_current_id)):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name, state, county, district, school FROM teacher_list WHERE regUserID = ?", id)
        teacher_data = cursor.fetchone()
        if teacher_data:
            name, state, county, district, school = teacher_data
            request.session["state"] = state
            request.session["county"] = county
            request.session["district"] = district
            request.session["school"] = school
            request.session["teacher"] = name
            return
        else:
            raise HTTPException(status_code=404, detail="Your account does not have a database listing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

def send_email(recipient_email: str, subject: str, message: str):
    try:
        sender = 'noReply.htheroes@gmail.com'
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient_email
        msg.attach(MIMEText(message, 'plain'))
        smtp_server = 'smtp.sendgrid.net'
        smtp_port = 465
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as smtp:
                smtp.login('apikey', os.environ.get('SENDGRID_API_KEY'))
                smtp.send_message(msg)
        except Exception as e:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')

def update_temp_password(email: str, new_password: str):
    try:
        hashed_password = sha256_crypt.hash(new_password)
        cursor = connection.cursor()
        cursor.execute("UPDATE registered_users SET password = ? WHERE CAST(email AS nvarchar) = ?", (hashed_password, email))
        connection.commit()
    except Exception as e:
        print(f"Error updating password: {e}")
        raise
        

#######apis#######
###api used to register a new user (and only a new user) into the new_user list
@app.post("/register/")
async def register_user(name: str = Form(...), email: str = Form(...), phone_number: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), state: str = Form(...),county: str = Form(...),district: str = Form(...), school: str = Form(...), role: str = Form(...)):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM registered_users WHERE CAST(email AS nvarchar) = ?", email)
        existing_user = cursor.fetchone()
        if existing_user:
            return {"message": "User with this email already exists."}
        cursor.execute("SELECT id FROM new_users WHERE CAST(email AS nvarchar) = ?", email)
        existing_user = cursor.fetchone()
        if existing_user:
            return {"message": "User with this email is already in the registration queue."}
        if password != confirm_password:
            return {"message": "Password do not match."}
        hashed_password = sha256_crypt.hash(password)
        insert_query = """
            INSERT INTO new_users (name, email, state, county, district, school, phone_number, password, role)
            VALUES (?, CAST(? AS NVARCHAR), ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (name, email, state, county, district, school, phone_number, hashed_password, role))
        connection.commit()
        send_email(email, "Registration successful",  f"Dear {email},\n\nThank you for registering with us! Once you are validated by a fellow teacher in your district or one of us here at HTHeroes, you will be able to create your profile and start receiving support.\n\nBest regards,\nHTHeroes Team")
        return {"message": "User registered successfully. You should recieve and email shortly."}
    except Exception as e:
        return {"message": "Registration unsuccessful", "error": str(e)}
    finally:
        cursor.close()

###api used to create cookie based session via authentication with registered_user table
@app.post("/login/")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, role, password, createCount FROM registered_users WHERE CAST(email AS NVARCHAR) = ?", (email,))
        user = cursor.fetchone()
        if user:
            hashed_password = user.password
            if sha256_crypt.verify(password, hashed_password):
                message = "Login successful as " + user.role
                request.session["user_email"] = email
                request.session["user_role"] = user.role
                request.session["user_id"] = user.id
                return JSONResponse(content={"message": message, "createCount": user.createCount, "role": user.role})
            else:
                message = "Invalid password."
        else:
            message = "Invalid email."
        return JSONResponse(content={"message": message}, status_code=400)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

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
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM new_users WHERE CAST(email AS NVARCHAR) = ?", user_email)
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in new_users")
        cursor.execute("INSERT INTO registered_users (email, password, role) "
                    "VALUES (?, ?, ?)",
                    (user.email, user.password, user.role))
        connection.commit()
        cursor.execute("DELETE FROM new_users WHERE CAST(email AS NVARCHAR) = ?", user_email)
        connection.commit()
        send_email(user.email, "Validation Notification", f"Dear {user.email},\n\nWe are pleased to inform you that your registration with us has been successfully validated! You may now log in and create your profile to start receiving support.\n\nIf you have any questions or need assistance, please do not hesitate to contact us.\n\nBest regards,\nHTHeroes Team")
        return {"message": "User validated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

##this api allows a logged in user to create an item in the table teacher_list in the hithero database if they have not created a user already
@app.post("/create_teacher_profile/")
async def create_teacher_profile(name: str = Form(...), state: str = Form(...), county: str = Form(...), district: str = Form(...), school: str = Form(...), aboutMe: str = Form(...), wishlist: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    try:
        if role:
            cursor = connection.cursor()
            cursor.execute("SELECT createCount FROM registered_users WHERE id = ?", id)
            link = cursor.fetchone()
            if link[0] == 0 or role == 'admin':
                aa_link = wishlist + "?&_encoding=UTF8&tag=hometownheroe-20"
                insert_query = "INSERT INTO teacher_list (name, state, county, district, school, regUserID, about_me, wishlist_url) " \
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                cursor.execute(insert_query, (name, state, county, district, school, id, aboutMe, aa_link))
                connection.commit()
                cursor.execute("UPDATE registered_users SET createCount = createCount + 1 WHERE id = ?", id)
                connection.commit()
                return {"message": "Teacher created successfully"}
            else:
                return {"message": "Unable to create new profile. Profile already created."}
        else:
            return {"message": "No user logged in."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

##api gets a random teacher from the list teacher_list in the hithero data base
@app.get("/random_teacher/")
async def get_random_teacher(request: Request):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT TOP 1 name, state, county, district, school FROM teacher_list ORDER BY NEWID()")
        random_teacher = cursor.fetchone()
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
            request.session["teacher"] = data["name"]
            return data
        else:
            raise HTTPException(status_code=404, detail="No teachers found in the database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

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

##api used to send contact us email from /contact.html
@app.post('/contact_us/')
async def contact_us(name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...)):
    recipient_email = 'hometown.heroes.contactus@gmail.com'
    full_message = f"{name}\n{email}\n{message}"
    try:
        result = send_email(recipient_email, subject, full_message)
        return {"message": result}
    except HTTPException as e:
        raise e
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
            state = get_index_cookie('state', request)
            county = get_index_cookie(index, request)
            cursor.execute("SELECT district FROM teacher_list WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ?", state, county)
        elif index == "district":
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie(index, request)
            cursor.execute("SELECT school FROM teacher_list WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND CAST(district AS nvarchar) = ?", state, county, district)
        elif index == "school":
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie(index, request)
            cursor.execute("SELECT name FROM teacher_list WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND CAST(district AS nvarchar) = ? AND CAST(school AS nvarchar) = ?", state, county, district, school)
        rows = cursor.fetchall()
        unique = set(row[0] for row in rows)
        result_list = list(unique)
        return result_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

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
        cursor.execute("SELECT wishlist_url, about_me, image_data FROM teacher_list WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND  CAST(district AS nvarchar) = ? AND CAST(school AS nvarchar) = ? AND CAST(name AS nvarchar) = ?", state, county, district, school, name)
        teacher_info = cursor.fetchone()
        if teacher_info:
            data = {
                "state": state,
                "county": county,
                "district": district,
                "school": school,
                "name": name,
                "wishlist_url": teacher_info[0],
                "about_me": teacher_info[1],
                #"image_data": teacher_info[2]
            }
            return data
        else:
            raise HTTPException(status_code=404, detail=f"Teacher not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()


###api used to update the logged in users teacher page. only info inpoutted is updated
@app.post("/update_teacher_info/")
async def edit_teacher_info(request: Request, wishlist: str = Form(...), aboutMe: str = Form(...), role: str = Depends(get_current_role)):
    try:
        if role:
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie('school', request) 
            name = get_index_cookie('teacher', request)
            cursor = connection.cursor()
            query = "UPDATE teacher_list SET"
            params = []
            if wishlist:
                aa_link = wishlist + "?&_encoding=UTF8&tag=hometownheroe-20"
                query += " wishlist_url = ?,"
                params.append(aa_link)
            if aboutMe:
                query += " about_me = ?,"
                params.append(aboutMe)
            query = query.rstrip(',') + " WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND CAST(district AS nvarchar) = ? AND CAST(school AS nvarchar) = ? AND CAST(name AS nvarchar) = ?"
            params.extend([state, county, district, school, name])
            cursor.execute(query, params)
            connection.commit()
            return {"message": "Information updated."}
        else:
            return {"message": "Permission denied."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()
    
###api used to update the logged in users teacher page image
@app.post("/update_teacher_image/")
async def edit_teacher_image(request: Request,role: str = Depends(get_current_role),image: UploadFile = Form(...)):
    try:
        if role:
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie('school', request)
            name = get_index_cookie('teacher', request)
            cursor = connection.cursor()
            query = """
                UPDATE teacher_list 
                SET image_data = ?
                WHERE CAST(state AS nvarchar) = ? 
                    AND CAST(county AS nvarchar) = ? 
                    AND CAST(district AS nvarchar) = ? 
                    AND CAST(school AS nvarchar) = ? 
                    AND CAST(name AS nvarchar) = ?
            """
            cursor.execute(query, (image.file.read(), state, county, district, school, name))
            connection.commit()
            return {"message": "Information updated."}
        else:
            return {"message": "Permission denied."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

##api gets your page based on the id in reg_users and and regUserID in teacher_list
@app.get("/myinfo/")
async def get_myinfo(request: Request, id: int = Depends(get_current_id)):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name, state, county, district, school FROM teacher_list WHERE regUserID = ?", id)
        teacher_data = cursor.fetchone()
        if teacher_data:
            name, state, county, district, school = teacher_data
            request.session["state"] = state
            request.session["county"] = county
            request.session["district"] = district
            request.session["school"] = school
            request.session["teacher"] = name
            return
        else:
            return {"message": "Your account does not have a database listing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

##api lets the logged in user update their password
@app.post("/update_password/")
async def update_password(request: Request, id: int = Depends(get_current_id), old_password: str = Form(...), new_password: str = Form(...), new_password_confirmed: str = Form(...)):
    try:
        if new_password == new_password_confirmed:
            cursor = connection.cursor()
            cursor.execute("SELECT password FROM registered_users WHERE id = ?", id)
            old_pass = cursor.fetchone()
            if old_pass and sha256_crypt.verify(old_password, old_pass[0]):
                hashed_new_password = sha256_crypt.hash(new_password)
                cursor.execute("UPDATE registered_users SET password = ? WHERE id = ?", (hashed_new_password, id))
                connection.commit()
                return {"status": "success", "message": "Password updated successfully"}
            else:
                return {"message": "Invalid old password"}
        else:
            return {"message": "New passwords do not match."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

#api to check if a user has edit acces to teacher page
@app.get("/check_access/")
async def check_access_teacher(request: Request, id: int = Depends(get_current_id), role: int = Depends(get_current_role)):
    try:
        cursor = connection.cursor()
        if role == 'teacher':
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie('school', request)
            name = get_index_cookie('teacher', request)

            cursor.execute("SELECT regUserID FROM teacher_list WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND CAST(district AS nvarchar) = ? AND CAST(school AS nvarchar) = ? AND CAST(name AS nvarchar) = ?", state, county, district, school, name)
            teacher_data = cursor.fetchone()
            if teacher_data and teacher_data[0] == id:
                return {"status": "success", "message": "Access granted"}
        raise HTTPException(status_code=403, detail="No access")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

#gets a list of unverified users to validate based on the role of the user
@app.get("/validation_list/")
async def validation_page(request: Request, role: str = Depends(get_current_role), id: int = Depends(get_current_id)):
    try:
        cursor = connection.cursor()
        if role == "admin":
            new_users = cursor.execute("SELECT * FROM new_users").fetchall()
            return {"new_users": [{"name": user.name, "email": user.email, "district": user.district, "school": user.school, "phone_number": user.phone_number} for user in new_users]}
        if role == 'teacher':
            store_my_cookies(request, id)
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            cursor.execute("SELECT * FROM new_users WHERE CAST(state AS nvarchar) = ? AND CAST(county AS nvarchar) = ? AND CAST(district AS nvarchar) = ?", (state, county, district))
            new_users = cursor.fetchall()
            return {"new_users": [{"name": user.name, "email": user.email, "districst": user.district, "school": user.school, "phone_number": user.phone_number} for user in new_users]}
        else:
            raise HTTPException(status_code=403, detail="You don't have permission to access this page.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")            
    finally:
        cursor.close()

#api gets a list of states from statecoutny table
@app.get("/get_states/")
async def get_states():
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT state FROM schools")
    states = cursor.fetchall()
    if states:
        state_names = sorted([state[0] for state in states])
        return state_names
    cursor.close()

#api gets the names of the counties in the desired state
@app.get("/get_counties/{state}")
async def get_counties(state: str):
    try:
        cursor = connection.cursor()
        query = "SELECT DISTINCT county FROM schools WHERE state = ?"
        cursor.execute(query, (state,))
        counties = cursor.fetchall()
        if counties:
            county_names = sorted([county[0] for county in counties])
            return county_names
        else:
            return {"message": f"No counties found for state: {state}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

#api gets the names of the school districts in the desired county and state
@app.get("/get_districts/{state}/{county}")
async def get_districts(state: str, county: str):
    try:
        cursor = connection.cursor()
        query = "SELECT DISTINCT district FROM schools WHERE state = ? AND county = ?"
        cursor.execute(query, (state, county))
        counties = cursor.fetchall()
        if counties:
            county_names = sorted([county[0] for county in counties])
            return county_names
        else:
            return {"message": f"No counties found for state: {state}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

#api gets the names of the school in the desired district, coutny, and state
@app.get("/get_schools/{state}/{county}/{district}")
async def get_schools(state: str, county: str, district: str):
    try:
        cursor = connection.cursor()
        query = "SELECT DISTINCT school_name FROM schools WHERE state = ? AND county = ? AND district = ?"
        cursor.execute(query, (state, county, district))
        counties = cursor.fetchall()
        if counties:
            county_names = sorted([county[0] for county in counties])
            return county_names
        else:
            return {"message": f"No counties found for state: {state}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()

#api for forgotten password reset, currently does not do anything exceptional
@app.post("/forgot_password/")
async def forgot_password(email: str = Form(...)):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM registered_users WHERE CAST(email AS NVARCHAR) = ?", email)
        user = cursor.fetchone()
        if user:
            recipient_email = email
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(10))
            full_message = f"Dear {email},\n\nWe have received a request for a password reset for your account. Here is your new temporary password: {temp_password}. Please use this password the next time you login and update it immediately.\n\nIf you did not request this password reset or have any concerns, please contact our support team.\n\nBest regards,\nHTHeroes Team"
            send_email(recipient_email, 'Forgot Pasword', full_message)
            update_temp_password(recipient_email, temp_password)
        else:
            time.sleep(1)
        message = "If account exists, instructions for password reset will be sent to your email. Check spam."
        return JSONResponse(content={"message": message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        cursor.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
