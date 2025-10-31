from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from config import get_db
from services.auth_service import AuthService
from dependencies import get_current_user_id
from utils.session import set_session_values, clear_session

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register/")
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    state: str = Form(...),
    county: str = Form(...),
    district: str = Form(...),
    school: str = Form(...),
    recaptcha_response: str = Form(...),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    user_data = {
        "name": name,
        "email": email,
        "phone_number": phone_number,
        "password": password,
        "confirm_password": confirm_password,
        "state": state,
        "county": county,
        "district": district,
        "school": school
    }
    result = auth_service.register_user(user_data, recaptcha_response)
    return result

@router.post("/login/")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    user_data = auth_service.login_user(email, password)
    
    # Set session values
    set_session_values(request, {
        "user_email": user_data["user_email"],
        "user_role": user_data["user_role"],
        "user_id": user_data["user_id"]
    })
    
    return JSONResponse(content={
        "message": f"Login successful as {user_data['user_role']}",
        "createCount": user_data["createCount"],
        "role": user_data["user_role"]
    })

@router.post("/logout/")
async def logout_user(request: Request):
    clear_session(request)
    return RedirectResponse(url="/", status_code=303)

@router.get("/profile/")
async def get_user_profile(
    request: Request,
    user_id: int = Depends(get_current_user_id)
):
    return JSONResponse(content={
        "user_id": request.session.get("user_id"),
        "user_role": request.session.get("user_role"),
        "user_email": request.session.get("user_email")
    })

@router.post("/forgot_password/")
async def forgot_password(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    result = auth_service.forgot_password(email)
    return JSONResponse(content=result)

@router.post("/update_password/")
async def update_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirmed: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    result = auth_service.update_password(
        user_id, old_password, new_password, new_password_confirmed
    )
    return result
