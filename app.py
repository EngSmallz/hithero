from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pyodbc

app = FastAPI()

# Define your AAD ODBC connection string
connection_string = (
    'Driver={ODBC Driver 18 for SQL Server};'
    'Server=tcp:hithero.database.windows.net,1433;'
    'Database=hithero_login;'
    'Uid=hithero_admin;' #temp to change file
    'Pwd=MedL&ke15;' #insert pass and delete before push
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

try:
    # Define the ODBC connection
    connection = pyodbc.connect(connection_string)
except pyodbc.Error as e:
    raise Exception(f"Error connecting to the database: {str(e)}")

# ...

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
async def login_user(email: str = Form(...), password: str = Form(...)):
    # Connect to the database
    cursor = connection.cursor()

    # Check if a user with the provided email and password exists in registered_users
    cursor.execute("SELECT id FROM registered_users WHERE CAST(email AS NVARCHAR) = ? AND CAST(password AS NVARCHAR) = ?", email, password)
    user = cursor.fetchone()

    if user:
        # User exists, you can return a success message or any user-specific data you need
        return {"message": "Login successful"}

    # User does not exist or password is incorrect, return an error
    raise HTTPException(status_code=400, detail="Invalid email or password")

    cursor.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)