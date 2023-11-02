from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pyodbc

app = FastAPI()

# Define SQLAlchemy models
Base = declarative_base()

# Define your AAD ODBC connection string
connection_string = (
    'Driver={ODBC Driver 18 for SQL Server};'
    'Server=tcp:hithero.database.windows.net,1433;'
    'Database=hithero_login;'
    'Uid=hithero_admin;'
    'Pwd=;'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)


try:
    # Define the ODBC connection
    connection = pyodbc.connect(connection_string)
except pyodbc.Error as e:
    raise Exception(f"Error connecting to the database: {str(e)}")

# Define a Pydantic model for user registration
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    role: str

@app.post("/register/")
def register_user(user_data: UserCreate):
    try:
        cursor = connection.cursor()

        # Check if a user with the provided email already exists in registered_users
        cursor.execute("SELECT id FROM registered_users WHERE email=?", user_data.email)
        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        # Check if a user with the provided email already exists in new_users
        cursor.execute("SELECT id FROM new_users WHERE email=?", user_data.email)
        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email is already in the registration queue")

        # Insert the new user into the "new_users" table
        cursor.execute("INSERT INTO new_users (first_name, last_name, email, phone_number, role) VALUES (?, ?, ?, ?, ?)", user_data.first_name, user_data.last_name, user_data.email, user_data.phone_number, user_data.role)
        connection.commit()

        cursor.close()
        return {"message": "User registered successfully"}
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
