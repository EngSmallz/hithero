from sqlalchemy.orm import Session
from repositories.spotlight_repository import SpotlightRepository
from repositories.teacher_repository import TeacherRepository
from repositories.user_repository import UserRepository
from services.email_service import EmailService
from fastapi import HTTPException
import base64
from typing import Dict, Optional

from services.twitter_service import TwitterService

class SpotlightService:
    def __init__(self, db: Session):
        self.db = db
        self.spotlight_repo = SpotlightRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.user_repo = UserRepository(db)
        self.email_service = EmailService()
    
    def get_spotlight_info(self, token: str) -> Dict:
        """Get spotlight information by token"""
        spotlight = self.spotlight_repo.find_by_token(token)
        
        if not spotlight:
            raise HTTPException(
                status_code=404,
                detail="Spotlight info not found"
            )
        
        image_data = None
        if spotlight.image_data:
            image_data = base64.b64encode(spotlight.image_data).decode('utf-8')
        
        return {
            "state": spotlight.state,
            "county": spotlight.county,
            "district": spotlight.district,
            "school": spotlight.school,
            "name": spotlight.name,
            "image_data": image_data
        }
    
    def store_spotlight(self, teacher_info: dict, token: str):
        """Store spotlight information"""
        spotlight_data = {"token": token}
        
        if token == "teacher":
            spotlight_data.update({
                "state": teacher_info["state"],
                "county": teacher_info["county"],
                "district": teacher_info["district"],
                "school": teacher_info["school"],
                "name": teacher_info["name"],
                "image_data": teacher_info.get("image_data")
            })
        elif token == "district":
            spotlight_data.update({
                "state": teacher_info["state"],
                "county": teacher_info["county"],
                "district": teacher_info["district"]
            })
        elif token == "county":
            spotlight_data.update({
                "state": teacher_info["state"],
                "county": teacher_info["county"]
            })
        
        self.spotlight_repo.upsert_spotlight(spotlight_data, token)
    
    def select_teacher_of_the_day(self):
        """Select a random teacher as teacher of the day"""
        random_teacher = self.teacher_repo.get_random_teacher()
        
        if not random_teacher:
            print("No random teacher found.")
            return
        
        teacher_info = {
            "name": random_teacher.name,
            "state": random_teacher.state,
            "county": random_teacher.county,
            "district": random_teacher.district,
            "school": random_teacher.school,
            "image_data": random_teacher.image_data,
            "url_id": random_teacher.url_id
        }
        
        # Store the teacher in spotlight
        self.store_spotlight(teacher_info, "teacher")

        #Try to send Tweet notification
        teacher_url = f"www.HelpTeachers.net/teacher/{random_teacher.url_id}"
        tweet_message = (
            f"Today's #TeacherOfTheDay is {random_teacher.name}! "
            f"You can support their classroom and mission here: {teacher_url}"
            f"#HomeroomHeroes #Education"
        )

        TwitterService().post_tweet(tweet_message)
        
        # Try to send email notification
        user = self.user_repo.find_registered_user_by_id(
            random_teacher.regUserID
        )
        
        if user:
            self.email_service.send_teacher_of_the_day_email(
                recipient_email=user.email,
                recipient_name=teacher_info["name"],
                url_id=teacher_info["url_id"]
            )
        else:
            print(f"No email found for teacher: {random_teacher.name}")
    
    def select_district_of_the_week(self):
        """Select a random district spotlight"""
        random_teacher = self.teacher_repo.get_random_teacher()
        
        if not random_teacher:
            print("No random teacher found.")
            return
        
        teacher_info = {
            "state": random_teacher.state,
            "county": random_teacher.county,
            "district": random_teacher.district
        }
        
        self.store_spotlight(teacher_info, "district")
    
    def select_county_of_the_month(self):
        """Select a random county spotlight"""
        random_teacher = self.teacher_repo.get_random_teacher()
        
        if not random_teacher:
            print("No random teacher found.")
            return
        
        teacher_info = {
            "state": random_teacher.state,
            "county": random_teacher.county
        }
        
        self.store_spotlight(teacher_info, "county")