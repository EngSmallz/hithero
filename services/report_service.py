from sqlalchemy.orm import Session
from repositories.teacher_repository import TeacherRepository
from repositories.user_repository import UserRepository
from services.email_service import EmailService
from fastapi import HTTPException
import os

class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.teacher_repo = TeacherRepository(db)
        self.user_repo = UserRepository(db)
        self.email_service = EmailService()
    
    def generate_teacher_report(
        self,
        state: str,
        county: str = None,
        district: str = None,
        school: str = None
    ):
        """Generate a teacher report and email it"""
        # Get teachers based on location
        teachers = self.teacher_repo.get_teachers_by_location(
            state, county, district, school
        )
        
        if not teachers:
            raise HTTPException(
                status_code=404,
                detail="No teachers found with the specified criteria"
            )
        
        # Get user details for each teacher
        teacher_data = []
        for teacher in teachers:
            # Need to get full teacher object for regUserID
            full_teacher = self.teacher_repo.find_by_url_id(teacher.url_id)
            if full_teacher:
                user = self.user_repo.find_registered_user_by_id(
                    full_teacher.regUserID
                )
                teacher_data.append({
                    "name": teacher.name,
                    "school": full_teacher.school,
                    "email": user.email if user else "N/A",
                    "phone": user.phone_number if user else "N/A"
                })
        
        # Generate report content
        report_lines = ["Name\tSchool\tEmail\tPhone"]
        for data in teacher_data:
            line = f"{data['name']}\t{data['school']}\t{data['email']}\t{data['phone']}"
            report_lines.append(line)
        
        file_content = "\n".join(report_lines)
        
        # Save report to file
        file_name = 'teacher_report.txt'
        file_path = os.path.join('./', file_name)
        
        with open(file_path, 'w') as f:
            f.write(file_content)
        
        # Send report via email
        self.email_service.send_attachment(
            recipient_email="homeroom.heroes.main@gmail.com",
            subject="Teacher Report",
            message="Please find the attached teacher report.",
            attachment_path=file_path
        )
        
        return {
            "message": f"Teacher report saved and sent via email. Located at {file_path}"
        }