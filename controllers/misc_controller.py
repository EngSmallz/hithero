from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from config import get_db, settings
from services.contact_service import ContactService
from services.report_service import ReportService
from dependencies import get_current_user_id
import os

router = APIRouter(tags=["miscellaneous"])

@router.post('/contact_us/')
async def contact_us(
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    recaptcha_response: str = Form(...)
):
    contact_service = ContactService()
    return contact_service.send_contact_message(
        name, email, subject, message, recaptcha_response
    )

@router.post("/generate_teacher_report/")
async def generate_teacher_report(
    state: str = Form(...),
    county: str = Form(None),
    district: str = Form(None),
    school: str = Form(None),
    db: Session = Depends(get_db)
):
    report_service = ReportService(db)
    return report_service.generate_teacher_report(
        state, county, district, school
    )

@router.get("/promo/{token}", response_class=HTMLResponse)
async def get_promotional_page(request: Request, token: str):
    """Sets session variable with promo token and redirects to homepage"""
    relative_image_path = settings.PROMO_IMAGE_MAPPING.get(token)
    
    if not relative_image_path:
        relative_image_path = settings.PROMO_IMAGE_MAPPING.get("default")
        if not relative_image_path:
            raise HTTPException(
                status_code=404,
                detail="Promotional image not found"
            )
    
    full_filesystem_path = os.path.join(
        settings.BASE_STATIC_DIR, relative_image_path
    )
    
    if not os.path.exists(full_filesystem_path):
        if token != "default":
            default_relative_path = settings.PROMO_IMAGE_MAPPING.get("default")
            if default_relative_path and os.path.exists(
                os.path.join(settings.BASE_STATIC_DIR, default_relative_path)
            ):
                relative_image_path = default_relative_path
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Image not found"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail="Default promotional image file not found"
            )
    
    # Store the static URL of the image in the session
    promo_image_url = f"/static/{relative_image_path}"
    request.session["promo_image_url"] = promo_image_url
    request.session["promo_title"] = "Working together to serve our communities!"
    
    return RedirectResponse(url="/pages/homepage.html")

@router.get("/get_promo_info/")
async def get_promo_info(request: Request):
    """Get and clear promo info from session"""
    promo_info = {
        "promo_image_url": request.session.pop("promo_image_url", None),
        "promo_title": request.session.pop("promo_title", None),
    }
    return JSONResponse(content=promo_info)