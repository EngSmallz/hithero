"""Account routes: registration, login/logout, session info, and password changes/resets."""
import logging
import secrets
import time
import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from passlib.hash import sha256_crypt
from sqlalchemy import String
from sqlalchemy.sql import select, cast, update

from app.database import SessionLocal
from app.dependencies import get_current_id, get_current_role, get_current_email
from app.limiter import limiter
from app.models import NewUsers, RegisteredUsers, PasswordResetToken
from app.services.emailer import render_email_template, send_email, send_registration_email
from app.utils import verify_recaptcha

logger = logging.getLogger(__name__)
router = APIRouter()

###api used to register a new user (and only a new user) into the new_user list
@router.post("/profile/register/")
@limiter.limit("5/minute")
async def register_user(request: Request, name: str = Form(...), email: str = Form(...), phone_number: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), state: str = Form(...),county: str = Form(...),district: str = Form(...), school: str = Form(...), recaptcha_response: str = Form(...)):
    # Verify reCAPTCHA
    if not verify_recaptcha(recaptcha_response):
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed. Please try again.")

    db = SessionLocal()
    try:
        query = select(RegisteredUsers.id).where(cast(RegisteredUsers.email, String) == cast(email, String))
        result = db.execute(query)
        existing_user = result.fetchone()
        if existing_user:
            return {"message": "User with this email already exists."}
        query = select(NewUsers.id).where(cast(NewUsers.email, String) == cast(email, String))
        result = db.execute(query)
        existing_user = result.fetchone()
        if existing_user:
            return {"message": "User with this email is already in the registration queue."}
        if password != confirm_password:
            return {"message": "Password do not match."}
        hashed_password = sha256_crypt.hash(password)
        role = 'teacher'
        new_user = NewUsers(name=name, email=email, state=state, county=county, district=district, school=school, phone_number=phone_number, password=hashed_password, role=role, report=0, emailed=0)
        db.add(new_user)
        db.commit()
        send_registration_email(email)
        return {"message": "User registered successfully. You should recieve an email shortly. Please check your spam folder"}
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {"message": "Registration unsuccessful. Please try again later."}

###api used to create cookie based session via authentication with registered_user table
@router.post("/profile/login/")
@limiter.limit("5/minute")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        query = select(RegisteredUsers).where(cast(RegisteredUsers.email, String) == cast(email, String))
        result = db.execute(query)
        user = result.fetchone()
        if user:
            hashed_password = user[0].password
            if sha256_crypt.verify(password, hashed_password):
                message = "Login successful as " + user[0].role
                request.session["user_email"] = email
                request.session["user_role"] = user[0].role
                request.session["user_id"] = user[0].id
                return JSONResponse(content={"message": message, "createCount": user[0].createCount, "role": user[0].role})
            else:
                message = "Invalid login credentials."
        else:
            message = "Invalid login credentials."
        return JSONResponse(content={"message": message})
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##end cookie session
@router.post("/profile/logout/")
async def logout_user(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
        del request.session["user_role"]
        del request.session["user_email"]
    return RedirectResponse(url="/", status_code=303)

###api gets the current session info of the logged in user
@router.get("/api/profile/")
async def get_user_profile(email: str = Depends(get_current_email), role: str = Depends(get_current_role), id: str = Depends(get_current_id)):
    if email:
        user_info = {
            "user_id": id,
            "user_role": role,
            "user_email": email
        }
        return JSONResponse(content=user_info)
    else:
        raise HTTPException(status_code=404, detail="No user logged in.")

##api lets the logged in user update their password
@router.post("/profile/update_password/")
async def update_password(request: Request, id: int = Depends(get_current_id), old_password: str = Form(...), new_password: str = Form(...), new_password_confirmed: str = Form(...)):
    db = SessionLocal()
    try:
        if new_password == new_password_confirmed:
            query = select(RegisteredUsers.password).where(RegisteredUsers.id == id)
            result = db.execute(query)
            old_pass = result.scalar()
            if old_pass and sha256_crypt.verify(old_password, old_pass):
                hashed_new_password = sha256_crypt.hash(new_password)
                update_query = update(RegisteredUsers).where(RegisteredUsers.id == id).values(password=hashed_new_password)
                db.execute(update_query)
                db.commit()
                return {"status": "success", "message": "Password updated successfully"}
            else:
                return {"message": "Invalid old password"}
        else:
            return {"message": "New passwords do not match."}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

@router.post("/profile/forgot_password/")
@limiter.limit("5/minute")
async def forgot_password(request: Request, email: str = Form(...)):
    db = SessionLocal()
    try:
        query = select(RegisteredUsers.id).where(cast(RegisteredUsers.email, String) == cast(email, String))
        result = db.execute(query)
        user = result.fetchone()
        if user:
            # Generate a secure token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            # Store the token
            reset_token = PasswordResetToken(email=email, token=token, expires_at=expires_at)
            db.add(reset_token)
            db.commit()
            # Send email with link instead of temp password
            reset_link = f"https://www.helpteachers.net/pages/reset_password.html?token={token}"
            template_data = {
                'recipient_name': email,
                'message_body': (
                    f"We received a request to reset your password. "
                    f"Click the link below to reset it (expires in 1 hour):\n\n"
                    f"{reset_link}\n\n"
                    f"If you did not request this, you can ignore this email."
                )
            }
            html_message = render_email_template('static/email_template.html', template_data)
            plain_message = f"Dear {email},\n\nReset your password here: {reset_link}\n\nExpires in 1 hour."
            send_email(email, 'Password Reset Request', html_message, plain_message)
        else:
            time.sleep(1)
        return JSONResponse(content={"message": "If an account exists, a reset link will be sent to your email."})
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

@router.post("/profile/reset_password/")
async def reset_password(token: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    db = SessionLocal()
    try:
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")
        # Look up the token
        reset = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == 0,
            PasswordResetToken.expires_at > datetime.datetime.utcnow()
        ).first()
        if not reset:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
        # Update the password
        hashed = sha256_crypt.hash(new_password)
        db.execute(update(RegisteredUsers).where(
            cast(RegisteredUsers.email, String) == cast(reset.email, String)
        ).values(password=hashed))
        # Mark token as used
        reset.used = 1
        db.commit()
        return JSONResponse(content={"message": "Password reset successfully. You can now log in."})
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()