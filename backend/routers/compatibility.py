import base64
import logging

from fastapi import APIRouter, Form, HTTPException, Request


def create_compatibility_router(
    *,
    fetch_random_teacher,
    set_teacher_session,
    verify_recaptcha,
    render_email_template,
    send_email,
    clean_html,
    logger: logging.Logger,
):
    """Register compatibility API actions used by SvelteKit and integrations."""
    router = APIRouter()

    @router.get("/api/random_teacher/")
    async def get_random_teacher(request: Request):
        try:
            teacher = fetch_random_teacher()
            if not teacher:
                raise HTTPException(
                    status_code=404,
                    detail="No teachers found in the database",
                )
            image_data = (
                base64.b64encode(teacher.image_data).decode("utf-8")
                if teacher.image_data
                else None
            )
            data = {
                "name": teacher.name,
                "state": teacher.state,
                "county": teacher.county,
                "district": teacher.district,
                "school": teacher.school,
                "image_data": image_data,
                "url_id": teacher.url_id,
            }
            set_teacher_session(request, teacher)
            return data
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error",
            )

    @router.post("/api/contact_us/")
    async def contact_us(
        name: str = Form(...),
        email: str = Form(...),
        subject: str = Form(...),
        message: str = Form(...),
        recaptcha_response: str = Form(...),
    ):
        if not verify_recaptcha(recaptcha_response):
            raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")

        clean_name = clean_html(name, tags=[], attributes={}, strip=True)
        clean_email = clean_html(email, tags=[], attributes={}, strip=True)
        clean_message = clean_html(message, tags=[], attributes={}, strip=True)
        clean_subject = clean_html(subject, tags=[], attributes={}, strip=True)

        template_data = {
            "recipient_name": "Homeroom Heroes Team",
            "message_body": f"Message from {clean_name} ({clean_email}):\n\n{clean_message}",
        }
        html_message = render_email_template(
            "static/email_template.html", template_data
        )
        plain_message = (
            f"Subject: {clean_subject}\n"
            f"Message from {clean_name} ({clean_email}):\n\n"
            f"{clean_message}"
        )

        try:
            sent = send_email(
                "Homeroom.heroes.contact@gmail.com",
                clean_subject,
                html_message,
                plain_message,
            )
            if not sent:
                raise HTTPException(
                    status_code=502,
                    detail="Contact email provider is temporarily unavailable.",
                )
            return {"message": "Email sent successfully!"}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error",
            )

    return router
