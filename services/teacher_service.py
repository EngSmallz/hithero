from config import settings
from models.database import RegisteredUsers
from sqlalchemy.orm import Session
from repositories.teacher_repository import TeacherRepository
from repositories.user_repository import UserRepository
from fastapi import HTTPException, UploadFile
import base64
import random

class TeacherService:
    def __init__(self, db: Session):
        self.db = db
        self.teacher_repo = TeacherRepository(db)
        self.user_repo = UserRepository(db)
    
    def create_teacher_profile(
        self, user_id: int, user_role: str, user_email: str, teacher_data: dict
    ):
        try:
            user = self.db.query(RegisteredUsers).filter_by(id=user_id).first()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if user.createCount > 0 and user_role != 'admin':
                raise HTTPException(
                    status_code=400,
                    detail="Profile already created"
                )
            
            # Generate URL ID
            first_part_email = user_email.split('@')[0]
            url_id = self._generate_unique_url_id(first_part_email)
            
            # Add Amazon affiliate tag
            aa_link = teacher_data["wishlist"] + "&tag=h0mer00mher0-20"
            
            teacher_insert_data = {
                "name": teacher_data["name"],
                "state": teacher_data["state"],
                "county": teacher_data["county"],
                "district": teacher_data["district"],
                "school": teacher_data["school"],
                "regUserID": user_id,
                "about_me": teacher_data["aboutMe"],
                "wishlist_url": aa_link,
                "url_id": url_id
            }
            
            self.teacher_repo.create_teacher(teacher_insert_data)
            self.user_repo.update_user_create_count(user_id)
            self.db.commit()
            
            return {"message": "Teacher created successfully", "role": user_role}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_teacher_info_by_session(
        self, state: str, county: str, district: str, school: str, name: str
    ):
        teacher = self.teacher_repo.find_by_location_and_name(
            state, county, district, school, name
        )
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        return self._format_teacher_response(teacher)
    
    def get_random_teacher(self):
        teacher = self.teacher_repo.get_random_teacher()
        
        if not teacher:
            raise HTTPException(
                status_code=404,
                detail="No teachers found"
            )
        
        return self._format_teacher_response(teacher)
    
    def get_teacher_by_url_id(self, url_id: str):
        teacher = self.teacher_repo.find_by_url_id(url_id)
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        return {
            "state": teacher.state,
            "county": teacher.county,
            "district": teacher.district,
            "school": teacher.school,
            "name": teacher.name
        }
    
    def update_teacher_info(self, user_id: int, about_me: str):
        try:
            self.teacher_repo.update_teacher(user_id, {"about_me": about_me})
            self.db.commit()
            return {"message": "Info updated"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_teacher_school(self, user_id: int, school_data: dict):
        try:
            self.teacher_repo.update_teacher(user_id, school_data)
            self.db.commit()
            return {"message": "School information updated"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_teacher_name(self, user_id: int, name: str):
        try:
            self.teacher_repo.update_teacher(user_id, {"name": name})
            self.db.commit()
            return {"message": "Name updated"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_wishlist(self, user_id: int, wishlist: str):
        try:
            aa_link = wishlist + "&tag=h0mer00mher0-20"
            self.teacher_repo.update_teacher(user_id, {"wishlist_url": aa_link})
            self.db.commit()
            return {"message": "Wishlist updated"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_url_id(self, user_id: int, url_id: str):
        # Check if URL ID already exists
        try:
            existing = self.teacher_repo.find_by_url_id(url_id)
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="URL ID already in use"
                )
            
            self.teacher_repo.update_teacher(user_id, {"url_id": url_id})
            self.db.commit()
            return {"message": "URL ID updated successfully"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_teacher_image(
        self, image: UploadFile, state: str, county: str,
        district: str, school: str, name: str
    ):
        try:
            if image.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail="File size exceeds limit"
                )
            
            image_data = image.file.read()
            self.teacher_repo.update_teacher_by_location(
                state, county, district, school, name,
                {"image_data": image_data}
            )
            self.db.commit()
            return {"message": "Image updated"}
        except HTTPException:
            self.db.rollback()  # Rollback on error
            raise
        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_my_teacher_info(self, user_id: int):
        teacher = self.teacher_repo.find_by_reg_user_id(user_id)
        
        if not teacher:
            raise HTTPException(
                status_code=404,
                detail="No database listing found"
            )
        
        return {
            "state": teacher.state,
            "county": teacher.county,
            "district": teacher.district,
            "school": teacher.school,
            "teacher": teacher.name
        }
    
    def check_teacher_access(
        self, user_id: int, state: str, county: str,
        district: str, school: str, name: str
    ) -> bool:
        teacher = self.teacher_repo.find_by_location_and_name(
            state, county, district, school, name
        )
        
        if not teacher or teacher.regUserID != user_id:
            return False
        
        return True
    
    def get_teacher_url(
        self, state: str, county: str, district: str, school: str, name: str
    ):
        teacher = self.teacher_repo.find_by_location_and_name(
            state, county, district, school, name
        )
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        return {"url": f"www.HelpTeachers.net/teacher/{teacher.url_id}"}
    
    def _generate_unique_url_id(self, base: str) -> str:
        url_id = f"{base}{random.randint(1, 9999)}"
        while self.teacher_repo.find_by_url_id(url_id):
            url_id = f"{base}{random.randint(1, 9999)}"
        return url_id
    
    def _format_teacher_response(self, teacher) -> dict:
        image_data = None
        if teacher.image_data:
            image_data = base64.b64encode(teacher.image_data).decode('utf-8')
        
        return {
            "name": teacher.name,
            "state": teacher.state,
            "county": teacher.county,
            "district": teacher.district,
            "school": teacher.school,
            "wishlist_url": teacher.wishlist_url,
            "about_me": teacher.about_me,
            "image_data": image_data
        }