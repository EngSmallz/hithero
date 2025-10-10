from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    password: str
    confirm_password: str
    state: str
    county: str
    district: str
    school: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str
    new_password_confirmed: str

class ForgotPassword(BaseModel):
    email: EmailStr