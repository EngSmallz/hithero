"""Site-level routes: ads.txt, sitemap.xml, the homepage redirect, and the contact form."""
import logging
import bleach
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.config import ADS_TXT_PATH, SITEMAP_XML_PATH
from app.services.emailer import render_email_template, send_email
from app.utils import verify_recaptcha

logger = logging.getLogger(__name__)
router = APIRouter()

# 1. Route for ads.txt (media_type='text/plain')
@router.get("/ads.txt", include_in_schema=False)
async def get_ads_txt():
    """Serves ads.txt from the static folder at the root URL."""
    return FileResponse(ADS_TXT_PATH, media_type='text/plain')

# 2. Route for sitemap.xml (media_type='application/xml')
@router.get("/sitemap.xml", include_in_schema=False)
async def get_sitemap_xml():
    """Serves sitemap.xml from the static folder at the root URL."""
    return FileResponse(SITEMAP_XML_PATH, media_type='application/xml')

## api used to send contact us email from /contact.html
@router.post('/api/contact_us/')
async def contact_us(name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...), recaptcha_response: str = Form(...)):

    # reCAPTCHA verification
    is_valid = verify_recaptcha(recaptcha_response)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")

    #clean and Define the data to populate the template
    clean_name = bleach.clean(name, tags=[], attributes={}, strip=True)
    clean_email = bleach.clean(email, tags=[], attributes={}, strip=True)
    clean_message = bleach.clean(message, tags=[], attributes={}, strip=True)
    clean_subject = bleach.clean(subject, tags=[], attributes={}, strip=True)

    template_data = {
        'recipient_name': 'Homeroom Heroes Team',
        'message_body': f"Message from {clean_name} ({clean_email}):\n\n{clean_message}"
    }

    # 1. Generate the HTML message from the template
    # The path is correctly specified relative to the project root
    html_message = render_email_template('static/email_template.html', template_data)

    # 2. Create a plain text fallback version
    plain_message = (
        f"Subject: {clean_subject}\n"
        f"Message from {clean_name} ({clean_email}):\n\n"
        f"{clean_message}"
    )

    recipient_email = 'Homeroom.heroes.contact@gmail.com'
    try:
        send_email(recipient_email, clean_subject, html_message, plain_message)
        return {"message": "Email sent successfully!"}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")

#homepage get
@router.get("/")
def read_root():
    return RedirectResponse("/pages/homepage.html")