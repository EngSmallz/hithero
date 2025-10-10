from services.email_service import EmailService
from fastapi import HTTPException
import requests
from config import settings

class ContactService:
    def __init__(self):
        self.email_service = EmailService()
    
    def verify_recaptcha(self, recaptcha_response: str) -> bool:
        """Verify reCAPTCHA response"""
        url = "https://www.google.com/recaptcha/api/siteverify"
        params = {
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": recaptcha_response
        }
        response = requests.post(url, params=params)
        data = response.json()
        return data.get("success", False)
    
    def send_contact_message(
        self,
        name: str,
        email: str,
        subject: str,
        message: str,
        recaptcha_response: str
    ):
        """Send contact form message"""
        # Verify reCAPTCHA
        if not self.verify_recaptcha(recaptcha_response):
            raise HTTPException(
                status_code=400,
                detail="Invalid reCAPTCHA"
            )
        
        # Prepare email
        template_data = {
            'recipient_name': 'Homeroom Heroes Team',
            'message_body': f"Message from {name} ({email}):\n\n{message}"
        }
        
        html_message = self.email_service.render_email_template(
            settings.EMAIL_TEMPLATE_PATH, template_data
        )
        
        plain_message = (
            f"Subject: {subject}\n"
            f"Message from {name} ({email}):\n\n"
            f"{message}"
        )
        
        self.email_service.send_email(
            recipient_email='Homeroom.heroes.contact@gmail.com',
            subject=subject,
            html_message=html_message,
            plain_message=plain_message
        )
        
        return {"message": "Email sent successfully!"}