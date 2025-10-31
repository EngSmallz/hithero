from services.email_service import EmailService
from utils.security import verify_recaptcha
from fastapi import HTTPException
from config import settings

class ContactService:
    def __init__(self):
        self.email_service = EmailService()
    
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
        if not verify_recaptcha(recaptcha_response):
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