import os
import base64
import brevo_python
from brevo_python.rest import ApiException
from config import settings
from typing import Optional

class EmailService:
    def __init__(self):
        self.configuration = brevo_python.Configuration()
        self.configuration.api_key['api-key'] = settings.BREVO_API_KEY
        self.api_instance = brevo_python.TransactionalEmailsApi(
            brevo_python.ApiClient(self.configuration)
        )
    
    def render_email_template(self, template_path: str, data: dict) -> str:
        """Loads an HTML template and replaces placeholders with data"""
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        for key, value in data.items():
            template_content = template_content.replace(
                f'{{{{ {key} }}}}', str(value)
            )
        
        return template_content
    
    def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_message: str,
        plain_message: str
    ):
        """
        Sends an email with HTML content and a plain text fallback using the Brevo API.
        """
        send_smtp_email = brevo_python.SendSmtpEmail(
            to=[{"email": recipient_email}],
            subject=subject,
            html_content=html_message,
            text_content=plain_message,
            sender={
                "name": settings.EMAIL_SENDER_NAME,
                "email": settings.EMAIL_SENDER_ADDRESS
            }
        )
        
        try:
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            print("Email sent successfully!")
            return api_response
        except ApiException as e:
            print(f"Exception when calling Brevo API: {e}")
            return None
    
    def send_attachment(
        self,
        recipient_email: str,
        subject: str,
        message: str,
        attachment_path: str
    ):
        """Sends an email with an attachment"""
        attachments = []
        if os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                file_data = f.read()
                encoded_content = base64.b64encode(file_data).decode('utf-8')
                
                attachments.append({
                    "content": encoded_content,
                    "name": os.path.basename(attachment_path)
                })
        else:
            print(f"Attachment file {attachment_path} not found.")
        
        send_smtp_email = brevo_python.SendSmtpEmail(
            to=[{"email": recipient_email}],
            subject=subject,
            html_content=f"<html><body>{message.replace('\\n', '<br>')}</body></html>",
            sender={
                "name": settings.EMAIL_SENDER_NAME,
                "email": settings.EMAIL_SENDER_ADDRESS
            },
            attachment=attachments
        )
        
        try:
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            print("Email sent successfully with attachment!")
            return api_response
        except ApiException as e:
            print(f"Exception when calling Brevo API[TransactionalEmailsApi->send_transac_email]: {e}")
            return None
    
    def send_registration_email(self, recipient_email: str):
        """Sends registration success email"""
        template_data = {
            'recipient_name': recipient_email,
            'message_body': (
                "Thank you for registering with us! Once you are validated by a "
                "fellow teacher in your district or one of us here at Homeroom Heroes, "
                "you will be able to create your profile and start receiving support."
            )
        }
        
        html_message = self.render_email_template(
            settings.EMAIL_TEMPLATE_PATH, template_data
        )
        
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "Best regards,\nHomeroom Heroes Team"
        )
        
        self.send_email(
            recipient_email,
            "Registration successful",
            html_message,
            plain_message
        )
    
    def send_validation_email(self, recipient_email: str):
        """Sends validation success email"""
        template_data = {
            'recipient_name': recipient_email,
            'message_body': (
                "We are pleased to inform you that your registration with us has been "
                "successfully validated! You may now log in and create your profile "
                "to start receiving support."
            )
        }
        
        html_message = self.render_email_template(
            settings.EMAIL_TEMPLATE_PATH, template_data
        )
        
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
            "Best regards,\nHomeroom Heroes Team"
        )
        
        self.send_email(
            recipient_email,
            "Validation Notification",
            html_message,
            plain_message
        )
    
    def send_password_reset_email(self, recipient_email: str, temp_password: str):
        """Sends password reset email with temporary password"""
        template_data = {
            'recipient_name': recipient_email,
            'message_body': (
                f"We have received a request for a password reset for your account. "
                f"Here is your new temporary password: <strong>{temp_password}</strong>. "
                f"Please use this password the next time you login and update it immediately.\n\n"
                f"If you did not request this password reset or have any concerns, "
                f"please contact our support team."
            )
        }
        
        html_message = self.render_email_template(
            settings.EMAIL_TEMPLATE_PATH, template_data
        )
        
        plain_message = (
            f"Dear {recipient_email},\n\n"
            f"We have received a request for a password reset for your account. "
            f"Here is your new temporary password: {temp_password}. "
            f"Please use this password the next time you login and update it immediately.\n\n"
            f"If you did not request this password reset or have any concerns, "
            f"please contact our support team.\n\n"
            f"Best regards,\nHomeroom Heroes Team"
        )
        
        self.send_email(
            recipient_email,
            'Forgot Password',
            html_message,
            plain_message
        )
    
    def send_teacher_of_the_day_email(
        self,
        recipient_email: str,
        recipient_name: str,
        url_id: str
    ):
        """Sends Teacher of the Day notification email"""
        template_data = {
            'recipient_name': recipient_name,
            'message_body': (
                "Congratulations! You've been chosen as today's 'Teacher of the Day' at Homeroom Heroes! "
                "Your profile is now featured on our homepage, giving you extra visibility. "
                "Remember to share your unique page with your community. "
                f"www.HelpTeachers.net/teacher/{url_id}"
            )
        }
        
        html_message = self.render_email_template(
            settings.EMAIL_TEMPLATE_PATH, template_data
        )
        
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "Best regards,\nHomeroom Heroes Team"
        )
        
        self.send_email(
            recipient_email,
            "🎉 You're Today's Homeroom Hero!",
            html_message,
            plain_message
        )
    
    def send_profile_reminder_email(self, recipient_email: str):
        """Sends profile creation reminder email"""
        template_data = {
            'recipient_name': recipient_email,
            'message_body': (
                "You're almost there! Your registration with us has been "
                "successfully validated, but you haven't created your profile yet. "
                "Please log in and complete your profile to start receiving support from our community.\n"
                "www.HelpTeachers.net/pages/login.html"
            )
        }
        
        html_message = self.render_email_template(
            settings.EMAIL_TEMPLATE_PATH, template_data
        )
        
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
            "Best regards,\nHomeroom Heroes Team"
        )
        
        self.send_email(
            recipient_email,
            "Reminder: Complete Your Homeroom Heroes Profile!",
            html_message,
            plain_message
        )
    
    def send_validation_reminder_email(self, recipient_email: str):
        """Sends validation reminder email to new users"""
        template_data = {
            'recipient_name': recipient_email,
            'message_body': (
                "Thanks for signing up! We noticed you haven't been validated yet. "
                "Please reach back out to us at homeroom.heroes.contact@gmail.com to complete your validation process."
            )
        }
        
        html_message = self.render_email_template(
            settings.EMAIL_TEMPLATE_PATH, template_data
        )
        
        plain_message = (
            f"Dear {template_data['recipient_name']},\n\n"
            f"{template_data['message_body']}\n\n"
            "Best regards,\nHomeroom Heroes Team"
        )
        
        self.send_email(
            recipient_email,
            "Reminder: Complete Your Homeroom Heroes Validation!",
            html_message,
            plain_message
        )