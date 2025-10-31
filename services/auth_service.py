from sqlalchemy.orm import Session
from models.database import RegisteredUsers
from repositories.user_repository import UserRepository
from utils.security import hash_password, verify_password, generate_temp_password, verify_recaptcha
from services.email_service import EmailService
from fastapi import HTTPException

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.email_service = EmailService()
    
    def register_user(self, user_data: dict, recaptcha_response: str):
        try:
            # Verify reCAPTCHA
            if not verify_recaptcha(recaptcha_response):
                raise HTTPException(
                    status_code=400, 
                    detail="reCAPTCHA verification failed"
                )
            
            # Check if user already exists
            if self.user_repo.find_registered_user_by_email(user_data["email"]):
                raise HTTPException(
                    status_code=400, 
                    detail="User with this email already exists"
                )
            
            if self.user_repo.find_new_user_by_email(user_data["email"]):
                raise HTTPException(
                    status_code=400,
                    detail="User already in registration queue"
                )
            
            # Validate passwords match
            if user_data["password"] != user_data["confirm_password"]:
                raise HTTPException(
                    status_code=400,
                    detail="Passwords do not match"
                )
            
            # Hash password and create user
            hashed_password = hash_password(user_data["password"])
            new_user_data = {
                "name": user_data["name"],
                "email": user_data["email"],
                "state": user_data["state"],
                "county": user_data["county"],
                "district": user_data["district"],
                "school": user_data["school"],
                "phone_number": user_data["phone_number"],
                "password": hashed_password,
                "role": "teacher",
                "report": 0,
                "emailed": 0
            }
            
            self.user_repo.create_new_user(new_user_data)
            self.email_service.send_registration_email(user_data["email"])
            
            return {"message": "User registered successfully"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def login_user(self, email: str, password: str):
        user = self.user_repo.find_registered_user_by_email(email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email")
        
        if not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        return {
            "user_id": user.id,
            "user_email": user.email,
            "user_role": user.role,
            "createCount": user.createCount
        }
    
    def forgot_password(self, email: str):
        try:
            user = self.user_repo.find_registered_user_by_email(email)
            
            if user:
                temp_password = generate_temp_password()
                hashed_password = hash_password(temp_password)
                self.user_repo.update_password(email, hashed_password)
                self.email_service.send_password_reset_email(email, temp_password)
            
            return {
                "message": "If account exists, password reset email sent"
            }
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_password(
        self, user_id: int, old_password: str, 
        new_password: str, new_password_confirmed: str
    ):
        try:
            if new_password != new_password_confirmed:
                raise HTTPException(
                    status_code=400,
                    detail="New passwords do not match"
                )
            
            user = self.db.query(RegisteredUsers).filter_by(id=user_id).first()
            
            if not user or not verify_password(old_password, user.password):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid old password"
                )
            
            hashed_password = hash_password(new_password)
            self.user_repo.update_password(user.email, hashed_password)
            
            return {"message": "Password updated successfully"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
