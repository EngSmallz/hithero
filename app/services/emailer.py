"""Email sending: the HTML template renderer, the Azure sender, and every email type the site sends."""
import os
from azure.communication.email import EmailClient

def render_email_template(template_path: str, data: dict) -> str:
    """
    Loads an HTML template and replaces placeholders with provided data.
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Replace placeholders with data values
    for key, value in data.items():
        template_content = template_content.replace(f'{{{{ {key} }}}}', str(value))
    
    return template_content

def send_email(recipient_email: str, subject: str, html_message: str, plain_message: str): ###AZURE REPLACEMENT###
    """
    Sends an email using Azure Communication Services Email.
    """
    try:
        connection_string = os.getenv("AZURE_EMAIL_CONNECTION_STRING")
        sender_address = os.getenv("AZURE_EMAIL_SENDER")

        client = EmailClient.from_connection_string(connection_string)

        message = {
            "senderAddress": sender_address,
            "recipients": {
                "to": [{"address": recipient_email}]
            },
            "content": {
                "subject": subject,
                "html": html_message,
                "plainText": plain_message
            }
        }

        poller = client.begin_send(message)
        result = poller.result()

        print("Azure email sent:", result)
        return True

    except Exception as ex:
        print("Azure email error:", ex)
        return False

def send_registration_email(recipient_email: str):
    """
    Prepares and sends the registration success email using the HTML template.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "Thank you for registering with us! Once you are validated by a "
            "fellow teacher in your district or one of us here at Homeroom Heroes, "
            "you will be able to create your profile and start receiving support."
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Registration successful",
        html_message,
        plain_message
    )

def send_validation_email(recipient_email: str):
    """
    Prepares and sends the validation success email using the HTML template.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "We are pleased to inform you that your registration with us has been "
            "successfully validated! You may now log in and create your profile "
            "to start receiving support."
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Validation Notification",
        html_message,
        plain_message
    )

def send_teacher_of_the_day_email(recipient_email: str, recipient_name: str, url_id: str):
    """
    Prepares and sends the 'Teacher of the Day' notification email.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_name,
        'message_body': (
            "Congratulations! You've been chosen as today's 'Teacher of the Day' at Homeroom Heroes! "
            "Your profile is now featured on our homepage, giving you extra visibility. "
            "Remember to share your unique page with your community. "
            f"www.HelpTeachers.net/teacher/{url_id}"
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "🎉 You're Today's Homeroom Hero!",
        html_message,
        plain_message
    )

def send_profile_reminder_email(recipient_email: str):
    """
    Sends a reminder email to a user to complete their profile.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "You're almost there! Your registration with us has been "
            "successfully validated, but you haven't created your profile yet. "
            "Please log in and complete your profile to start receiving support from our community.\n"
            "www.HelpTeachers.net/pages/login.html"
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "If you have any questions or need assistance, please do not hesitate to contact us.\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Reminder: Complete Your Homeroom Heroes Profile!",
        html_message,
        plain_message
    )

def send_validation_reminder_email(recipient_email: str):
    """
    Sends a reminder email to a new user to reach out for validation.
    """
    # Define the data to populate the template
    template_data = {
        'recipient_name': recipient_email,
        'message_body': (
            "Thanks for signing up! We noticed you haven't been validated yet. "
            "Please reach back out to us at homeroom.heroes.contact@gmail.com to complete your validation process."
        )
    }

    # Generate the HTML message from the template
    html_message = render_email_template('static/email_template.html', template_data)

    # Create a plain text fallback version
    plain_message = (
        f"Dear {template_data['recipient_name']},\n\n"
        f"{template_data['message_body']}\n\n"
        "Best regards,\nHomeroom Heroes Team\nhomeroom.heroes.contact@gmail.com"
    )

    # Call the core send_email function
    send_email(
        recipient_email,
        "Reminder: Complete Your Homeroom Heroes Validation!",
        html_message,
        plain_message
    )