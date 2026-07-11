import datetime
import re
import secrets
import time

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from passlib.hash import sha256_crypt
from sqlalchemy import String, cast, insert, select, update

from backend.repositories.profile import ProfileRepository
from backend.services.profile_mutations import ProfileMutationService
from backend.services.profile_reads import ProfileReadService


def create_profile_router(
    *,
    session_factory,
    pending_user_model,
    registered_user_model,
    teacher_model,
    reset_token_model,
    get_current_id,
    get_current_role,
    get_current_email,
    get_index_cookie,
    set_teacher_session,
    verify_recaptcha,
    send_registration_email,
    render_email_template,
    send_email,
    limiter,
    detect_file_type,
    max_file_size,
    logger,
):
    router = APIRouter()
    profile_repository = ProfileRepository(
        session_factory=session_factory,
        teacher_model=teacher_model,
    )
    profile_read_service = ProfileReadService(profile_repository)
    profile_mutation_service = ProfileMutationService(profile_repository)

    @router.post("/profile/register/")
    @limiter.limit("5/minute")
    async def register_user(
        request: Request,
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
    ):
        if not verify_recaptcha(recaptcha_response):
            raise HTTPException(
                status_code=400,
                detail="reCAPTCHA verification failed. Please try again.",
            )

        db = session_factory()
        try:
            existing_user = db.execute(
                select(registered_user_model.id).where(
                    cast(registered_user_model.email, String)
                    == cast(email, String)
                )
            ).fetchone()
            if existing_user:
                return {"message": "User with this email already exists."}

            pending_user = db.execute(
                select(pending_user_model.id).where(
                    cast(pending_user_model.email, String)
                    == cast(email, String)
                )
            ).fetchone()
            if pending_user:
                return {
                    "message": (
                        "User with this email is already in the registration queue."
                    )
                }
            if password != confirm_password:
                return {"message": "Password do not match."}

            db.add(
                pending_user_model(
                    name=name,
                    email=email,
                    state=state,
                    county=county,
                    district=district,
                    school=school,
                    phone_number=phone_number,
                    password=sha256_crypt.hash(password),
                    role="teacher",
                    report=0,
                    emailed=0,
                )
            )
            db.commit()
            send_registration_email(email)
            return {
                "message": (
                    "User registered successfully. You should recieve an email "
                    "shortly. Please check your spam folder"
                )
            }
        except Exception as exc:
            logger.error(f"Registration error: {str(exc)}")
            return {
                "message": "Registration unsuccessful. Please try again later."
            }

    @router.post("/profile/login/")
    @limiter.limit("5/minute")
    async def login_user(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
    ):
        db = session_factory()
        try:
            user = db.execute(
                select(registered_user_model).where(
                    cast(registered_user_model.email, String)
                    == cast(email, String)
                )
            ).fetchone()
            if user and sha256_crypt.verify(password, user[0].password):
                request.session["user_email"] = email
                request.session["user_role"] = user[0].role
                request.session["user_id"] = user[0].id
                return JSONResponse(
                    content={
                        "message": f"Login successful as {user[0].role}",
                        "createCount": user[0].createCount,
                        "role": user[0].role,
                    }
                )
            return JSONResponse(content={"message": "Invalid login credentials."})
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/profile/logout/")
    async def logout_user(request: Request):
        if "user_id" in request.session:
            del request.session["user_id"]
            del request.session["user_role"]
            del request.session["user_email"]
        return RedirectResponse(url="/", status_code=303)

    @router.post("/profile/create_teacher_profile/")
    async def create_teacher_profile(
        request: Request,
        name: str = Form(...),
        state: str = Form(...),
        county: str = Form(...),
        district: str = Form(...),
        school: str = Form(...),
        aboutMe: str = Form(...),
        wishlist: str = Form(...),
        user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        db = session_factory()
        try:
            if not role:
                return {"message": "No user logged in."}

            create_count = db.execute(
                select(registered_user_model.createCount).where(
                    registered_user_model.id == user_id
                )
            ).scalar()
            if create_count != 0 and role != "admin":
                return {
                    "message": (
                        "Unable to create new profile. Profile already created."
                    )
                }

            affiliate_link = wishlist + "&tag=h0mer00mher0-20"
            email = get_current_email(request)
            first_part_email = email.split("@")[0]
            auto_url_id = f"{first_part_email}{secrets.randbelow(9999)}"
            while db.execute(
                select(teacher_model).where(
                    cast(teacher_model.url_id, String)
                    == cast(auto_url_id, String)
                )
            ).first():
                auto_url_id = f"{first_part_email}{secrets.randbelow(9999)}"

            db.execute(
                insert(teacher_model).values(
                    name=name,
                    state=state,
                    county=county,
                    district=district,
                    school=school,
                    regUserID=user_id,
                    about_me=aboutMe,
                    wishlist_url=affiliate_link,
                    url_id=auto_url_id,
                )
            )
            db.execute(
                update(registered_user_model)
                .where(registered_user_model.id == user_id)
                .values(
                    createCount=registered_user_model.createCount + 1
                )
            )
            db.commit()
            return {"message": "Teacher created successfully", "role": role}
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.get("/api/profile/")
    async def get_user_profile(
        email: str = Depends(get_current_email),
        role: str = Depends(get_current_role),
        user_id: str = Depends(get_current_id),
    ):
        if email:
            return JSONResponse(
                content={
                    "user_id": user_id,
                    "user_role": role,
                    "user_email": email,
                }
            )
        raise HTTPException(status_code=404, detail="No user logged in.")

    @router.get("/api/get_teacher_info/")
    async def get_teacher_info(request: Request):
        try:
            teacher_info = profile_read_service.get_teacher_info(
                {
                    field: get_index_cookie(field, request)
                    for field in ("state", "county", "district", "school", "teacher")
                }
            )
            if teacher_info is None:
                raise HTTPException(status_code=404, detail="Teacher not found")
            return teacher_info
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.post("/profile/update_info/")
    async def update_info(
        request: Request,
        aboutMe: str = Form(...),
        user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        db = session_factory()
        try:
            if not role:
                raise HTTPException(status_code=403, detail="Permission denied.")
            db.execute(
                update(teacher_model)
                .where(teacher_model.regUserID == user_id)
                .values(about_me=aboutMe)
            )
            db.commit()
            return {"message": "Info updated."}
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/profile/update_teacher_school/")
    async def update_teacher_school(
        request: Request,
        state: str = Form(...),
        county: str = Form(...),
        district: str = Form(...),
        school: str = Form(...),
        user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        try:
            if not role:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied. Not logged in.",
                )
            profile_mutation_service.update_teacher_school(
                user_id,
                state=state,
                county=county,
                district=district,
                school=school,
            )
            return JSONResponse(
                content={
                    "message": "School information updated successfully."
                }
            )
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.post("/profile/update_teacher_name/")
    async def update_teacher_name(
        request: Request,
        teacher: str = Form(...),
        user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        try:
            if not role:
                raise HTTPException(status_code=403, detail="Permission denied.")
            profile_mutation_service.update_teacher_name(user_id, teacher)
            return {"message": "Name updated."}
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.post("/profile/update_wishlist/")
    async def update_wishlist(
        request: Request,
        wishlist: str = Form(...),
        user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        try:
            if not role:
                raise HTTPException(status_code=403, detail="Permission denied.")
            profile_mutation_service.update_teacher_wishlist(user_id, wishlist)
            return {"message": "Wishlist updated."}
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.post("/profile/update_url_id/")
    async def update_url_id(
        request: Request,
        url_id: str = Form(...),
        user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        db = session_factory()
        try:
            if not role:
                raise HTTPException(status_code=403, detail="Permission denied.")
            if not re.match(r"^[a-zA-Z0-9_-]{3,50}$", url_id):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "URL ID may only contain letters, numbers, hyphens, "
                        "and underscores (3–50 characters)."
                    ),
                )
            existing_teacher = (
                db.query(teacher_model)
                .where(
                    cast(teacher_model.url_id, String)
                    == cast(url_id, String)
                )
                .first()
            )
            if existing_teacher:
                raise HTTPException(
                    status_code=409,
                    detail="URL ID already in use.",
                )
            db.execute(
                update(teacher_model)
                .where(teacher_model.regUserID == user_id)
                .values(url_id=url_id)
            )
            db.commit()
            return {"message": "URL ID updated successfully."}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/profile/update_teacher_image/")
    async def edit_teacher_image(
        request: Request,
        role: str = Depends(get_current_role),
        image: UploadFile = Form(...),
        user_id: int = Depends(get_current_id),
    ):
        db = session_factory()
        try:
            if image.size > max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail="File size exceeds the allowed limit",
                )

            image_bytes = await image.read()
            allowed_mime_types = {
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
            }
            results = detect_file_type(image_bytes)
            detected_type = None
            if results:
                detected_type = getattr(results[0], "mime", None)
                if detected_type is None:
                    detected_type = getattr(results[0], "mime_type", None)
            if detected_type not in allowed_mime_types:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid file type. Only JPEG, PNG, GIF, and WebP "
                        "are allowed."
                    ),
                )

            if role:
                db.execute(
                    update(teacher_model)
                    .values(image_data=image_bytes)
                    .where(teacher_model.regUserID == user_id)
                )
                db.commit()
                return {"message": "Information updated."}
            return {"message": "Permission denied."}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.get("/profile/myinfo/")
    async def get_myinfo(
        request: Request,
        user_id: int = Depends(get_current_id),
    ):
        try:
            teacher_data = profile_read_service.get_myinfo(user_id)
            if teacher_data:
                teacher, session_data = teacher_data
                set_teacher_session(request, teacher)
                return session_data
            return {
                "message": "Your account does not have a database listing"
            }
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.post("/profile/update_password/")
    async def update_password(
        request: Request,
        user_id: int = Depends(get_current_id),
        old_password: str = Form(...),
        new_password: str = Form(...),
        new_password_confirmed: str = Form(...),
    ):
        db = session_factory()
        try:
            if new_password != new_password_confirmed:
                return {"message": "New passwords do not match."}

            old_password_hash = db.execute(
                select(registered_user_model.password).where(
                    registered_user_model.id == user_id
                )
            ).scalar()
            if (
                not old_password_hash
                or not sha256_crypt.verify(old_password, old_password_hash)
            ):
                return {"message": "Invalid old password"}

            db.execute(
                update(registered_user_model)
                .where(registered_user_model.id == user_id)
                .values(password=sha256_crypt.hash(new_password))
            )
            db.commit()
            return {
                "status": "success",
                "message": "Password updated successfully",
            }
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.get("/api/check_access_teacher/")
    async def check_access_teacher(
        request: Request,
        user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        try:
            context = {
                field: get_index_cookie(field, request)
                for field in ("state", "county", "district", "school", "teacher")
            }
            if profile_read_service.has_teacher_access(context, user_id, role):
                return {"status": "success", "message": "Access granted"}
            raise HTTPException(status_code=403, detail="No access")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.post("/profile/forgot_password/")
    @limiter.limit("5/minute")
    async def forgot_password(
        request: Request,
        email: str = Form(...),
    ):
        db = session_factory()
        try:
            user = db.execute(
                select(registered_user_model.id).where(
                    cast(registered_user_model.email, String)
                    == cast(email, String)
                )
            ).fetchone()
            if user:
                token = secrets.token_urlsafe(32)
                expires_at = (
                    datetime.datetime.utcnow()
                    + datetime.timedelta(hours=1)
                )
                db.add(
                    reset_token_model(
                        email=email,
                        token=token,
                        expires_at=expires_at,
                    )
                )
                db.commit()
                reset_link = (
                    "https://www.helpteachers.net/reset-password"
                    f"?token={token}"
                )
                template_data = {
                    "recipient_name": email,
                    "message_body": (
                        "We received a request to reset your password. "
                        "Click the link below to reset it (expires in 1 hour):"
                        f"\n\n{reset_link}\n\n"
                        "If you did not request this, you can ignore this email."
                    ),
                }
                send_email(
                    email,
                    "Password Reset Request",
                    render_email_template(
                        "static/email_template.html",
                        template_data,
                    ),
                    (
                        f"Dear {email},\n\nReset your password here: "
                        f"{reset_link}\n\nExpires in 1 hour."
                    ),
                )
            else:
                time.sleep(1)
            return JSONResponse(
                content={
                    "message": (
                        "If an account exists, a reset link will be sent "
                        "to your email."
                    )
                }
            )
        except Exception as exc:
            db.rollback()
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/profile/reset_password/")
    async def reset_password(
        token: str = Form(...),
        new_password: str = Form(...),
        confirm_password: str = Form(...),
    ):
        db = session_factory()
        try:
            if new_password != confirm_password:
                raise HTTPException(
                    status_code=400,
                    detail="Passwords do not match.",
                )
            reset = (
                db.query(reset_token_model)
                .filter(
                    reset_token_model.token == token,
                    reset_token_model.used == 0,
                    reset_token_model.expires_at
                    > datetime.datetime.utcnow(),
                )
                .first()
            )
            if not reset:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or expired reset token.",
                )

            db.execute(
                update(registered_user_model)
                .where(
                    cast(registered_user_model.email, String)
                    == cast(reset.email, String)
                )
                .values(password=sha256_crypt.hash(new_password))
            )
            reset.used = 1
            db.commit()
            return JSONResponse(
                content={
                    "message": (
                        "Password reset successfully. You can now log in."
                    )
                }
            )
        except HTTPException:
            raise
        except Exception as exc:
            db.rollback()
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.get("/api/teacher_url/")
    async def get_teacher_url(request: Request):
        try:
            url = profile_read_service.get_teacher_url(
                {
                    field: get_index_cookie(field, request)
                    for field in ("state", "county", "district", "school", "teacher")
                }
            )
            if url is None:
                raise HTTPException(
                    status_code=404,
                    detail="No matching teacher found",
                )
            return {"url": url}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    return router
