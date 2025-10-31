from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from repositories.teacher_repository import TeacherRepository
from services.email_service import EmailService
from fastapi import HTTPException
from typing import List, Dict

class ValidationService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.email_service = EmailService()
    
    def get_validation_list(self, user_role: str, user_id: int) -> Dict:
        """Get list of users awaiting validation based on role"""
        if user_role == "admin":
            new_users = self.user_repo.get_all_new_users()
        elif user_role == "teacher":
            # Get teacher's location
            teacher = self.teacher_repo.find_by_reg_user_id(user_id)
            if not teacher:
                raise HTTPException(
                    status_code=404,
                    detail="Teacher profile not found"
                )
            
            new_users = self.user_repo.get_new_users_by_location(
                teacher.state, teacher.county, teacher.district
            )
        else:
            raise HTTPException(
                status_code=403,
                detail="No permission to access validation"
            )
        
        user_list = [
            {
                "name": user.name,
                "email": user.email,
                "state": user.state,
                "district": user.district,
                "school": user.school,
                "phone_number": user.phone_number,
                "report": user.report,
                "emailed": user.emailed
            }
            for user in new_users
        ]
        
        return {"new_users": user_list, "role": user_role}
    
    def validate_user(self, user_email: str):
        """Move user from new_users to registered_users"""
        try:
            new_user = self.user_repo.find_new_user_by_email(user_email)
            
            if not new_user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found in new_users"
                )
            
            # Create registered user
            registered_user_data = {
                "email": new_user.email,
                "password": new_user.password,
                "role": new_user.role,
                "phone_number": new_user.phone_number,
                "createCount": 0
            }
            
            self.user_repo.create_registered_user(registered_user_data)
            self.user_repo.delete_new_user(user_email)
            
            # Send validation email
            self.email_service.send_validation_email(new_user.email)

            self.db.commit()
            
            return {"message": "User validated"}
    
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
    
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_user(self, user_email: str):
        """Delete user from new_users table"""
        try:
            new_user = self.user_repo.find_new_user_by_email(user_email)
            
            if not new_user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found in new_users"
                )
            
            self.user_repo.delete_new_user(user_email)
            self.db.commit()
            return {"message": "User deleted successfully"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def report_user(self, user_email: str):
        """Mark user as reported"""
        try:
            self.user_repo.update_new_user_report(user_email)
            self.db.commit()
            return {"message": "User reported"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def mark_user_emailed(self, user_email: str):
        """Mark that user has been emailed"""
        try:
            self.user_repo.update_new_user_emailed(user_email)
            self.db.commit()
            return {"message": "User marked as emailed"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))