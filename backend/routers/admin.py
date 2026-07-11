import os
import tempfile

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy import String, cast, delete, insert, select, update

from backend.repositories.admin import AdminRepository
from backend.services.admin import (
    AdminService,
    PendingUserNotFound,
    UserAccountNotFound,
)


def create_admin_router(
    *,
    session_factory,
    pending_user_model,
    registered_user_model,
    teacher_model,
    get_current_id,
    get_current_role,
    set_teacher_session,
    get_index_cookie,
    send_validation_email,
    send_attachment,
    logger,
    get_admin_secret,
):
    router = APIRouter()
    account_repository = AdminRepository(
        session_factory=session_factory,
        registered_user_model=registered_user_model,
        teacher_model=teacher_model,
        pending_user_model=pending_user_model,
    )
    admin_service = AdminService(account_repository)

    def serialize_pending_users(rows):
        return [
            {
                "name": row[0].name,
                "email": row[0].email,
                "state": row[0].state,
                "district": row[0].district,
                "school": row[0].school,
                "phone_number": row[0].phone_number,
                "report": row[0].report,
                "emailed": row[0].emailed,
            }
            for row in rows
        ]

    def require_teacher_scope(db, request, role, user_email):
        if role == "admin":
            return

        pending_user = db.execute(
            select(pending_user_model).where(
                cast(pending_user_model.email, String)
                == cast(user_email, String)
            )
        ).fetchone()
        teacher = db.execute(
            select(teacher_model).where(
                teacher_model.regUserID == get_current_id(request)
            )
        ).fetchone()
        if not pending_user or not teacher or (
            pending_user[0].state != teacher[0].state
            or pending_user[0].county != teacher[0].county
            or pending_user[0].district != teacher[0].district
        ):
            raise HTTPException(
                status_code=403,
                detail="You can only moderate teachers in your own district.",
            )

    @router.post("/validation/validate_user/{user_email}")
    async def move_user(
        user_email: str,
        request: Request,
        role: str = Depends(get_current_role),
    ):
        if role not in ("admin", "teacher"):
            raise HTTPException(status_code=403, detail="Access denied.")

        db = session_factory()
        try:
            user = db.execute(
                select(pending_user_model).where(
                    cast(pending_user_model.email, String)
                    == cast(user_email, String)
                )
            ).fetchone()
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found in new_users",
                )

            if role == "teacher":
                user_id = get_current_id(request)
                teacher_record = db.execute(
                    select(teacher_model).where(
                        teacher_model.regUserID == user_id
                    )
                ).fetchone()
                if not teacher_record or (
                    user[0].state != teacher_record[0].state
                    or user[0].county != teacher_record[0].county
                    or user[0].district != teacher_record[0].district
                ):
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            "You can only validate teachers in your own district."
                        ),
                    )

            db.execute(
                insert(registered_user_model).values(
                    email=user[0].email,
                    password=user[0].password,
                    role=user[0].role,
                    phone_number=user[0].phone_number,
                )
            )
            db.execute(
                delete(pending_user_model).where(
                    cast(pending_user_model.email, String)
                    == cast(user_email, String)
                )
            )
            db.commit()
            send_validation_email(user[0].email)
            return {"message": "User validated."}
        except HTTPException:
            raise
        except Exception as exc:
            db.rollback()
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.get("/api/validation_list/")
    async def validation_page(
        request: Request,
        role: str = Depends(get_current_role),
        user_id: int = Depends(get_current_id),
    ):
        db = session_factory()
        try:
            if role == "admin":
                new_users = db.execute(select(pending_user_model)).fetchall()
                return {
                    "new_users": serialize_pending_users(new_users),
                    "role": role,
                }

            if role == "teacher":
                teacher_data = db.execute(
                    select(teacher_model).where(
                        teacher_model.regUserID == user_id
                    )
                ).fetchone()
                if not teacher_data:
                    return {"new_users": [], "role": role}

                set_teacher_session(request, teacher_data[0])
                state = get_index_cookie("state", request)
                county = get_index_cookie("county", request)
                district = get_index_cookie("district", request)
                new_users = db.execute(
                    select(pending_user_model).where(
                        (cast(pending_user_model.state, String) == state)
                        & (cast(pending_user_model.county, String) == county)
                        & (cast(pending_user_model.district, String) == district)
                    )
                ).fetchall()
                return {
                    "new_users": serialize_pending_users(new_users),
                    "role": role,
                }

            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this page.",
            )
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/validation/delete_user/{user_email}")
    async def delete_user(
        user_email: str,
        role: str = Depends(get_current_role),
    ):
        if role != "admin":
            raise HTTPException(
                status_code=403,
                detail="No permission to to action.",
            )

        try:
            admin_service.delete_pending_user(user_email)
            return {"message": "User deleted successfully."}
        except PendingUserNotFound:
            raise HTTPException(status_code=404, detail="User not found in new_users")
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.post("/validation/report_user/{user_email}")
    async def report_user(
        user_email: str,
        request: Request,
        role: str = Depends(get_current_role),
    ):
        if role not in ("admin", "teacher"):
            raise HTTPException(status_code=403, detail="Access denied.")

        db = session_factory()
        try:
            require_teacher_scope(db, request, role, user_email)
            db.execute(
                update(pending_user_model)
                .where(
                    cast(pending_user_model.email, String)
                    == cast(user_email, String)
                )
                .values(report=1)
            )
            db.commit()
            return {"message": "User reported."}
        except Exception as exc:
            db.rollback()
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/validation/emailed_user/{user_email}")
    async def emailed_user(
        user_email: str,
        request: Request,
        role: str = Depends(get_current_role),
    ):
        if role not in ("admin", "teacher"):
            raise HTTPException(status_code=403, detail="Access denied.")

        db = session_factory()
        try:
            require_teacher_scope(db, request, role, user_email)
            db.execute(
                update(pending_user_model)
                .where(
                    cast(pending_user_model.email, String)
                    == cast(user_email, String)
                )
                .values(emailed=1)
            )
            db.commit()
            return {"message": "User emailed."}
        except Exception as exc:
            db.rollback()
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/admin/generate_teacher_report/")
    async def generate_teacher_report(
        state: str = Form(...),
        county: str = Form(None),
        district: str = Form(None),
        school: str = Form(None),
        role: str = Depends(get_current_role),
    ):
        if role != "admin":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Access denied: Only administrators can generate reports."
                ),
            )

        db = session_factory()
        try:
            query = select(
                teacher_model.name,
                teacher_model.school,
                teacher_model.regUserID,
            ).where(cast(teacher_model.state, String) == state)
            if county:
                query = query.where(cast(teacher_model.county, String) == county)
            if district:
                query = query.where(
                    cast(teacher_model.district, String) == district
                )
            if school:
                query = query.where(cast(teacher_model.school, String) == school)

            teachers = db.execute(query).fetchall()
            if not teachers:
                raise HTTPException(
                    status_code=404,
                    detail="No teachers found with the specified criteria.",
                )

            reg_user_ids = [teacher.regUserID for teacher in teachers]
            users = db.execute(
                select(
                    registered_user_model.id,
                    registered_user_model.email,
                    registered_user_model.phone_number,
                ).where(registered_user_model.id.in_(reg_user_ids))
            ).fetchall()

            data = ["Name\tSchool\tEmail\tPhone"]
            user_dict = {
                user.id: {"email": user.email, "phone": user.phone_number}
                for user in users
            }
            for teacher in teachers:
                user = user_dict.get(teacher.regUserID, {})
                data.append(
                    f"{teacher.name}\t{teacher.school}\t"
                    f"{user.get('email', 'N/A')}\t{user.get('phone', 'N/A')}"
                )

            with tempfile.NamedTemporaryFile(
                mode="w",
                prefix="teacher-report-",
                suffix=".txt",
                delete=False,
            ) as temp_file:
                temp_file.write("\n".join(data))
                file_path = temp_file.name

            try:
                send_attachment(
                    recipient_email="homeroom.heroes.main@gmail.com",
                    subject="Teacher Report",
                    message="Please find the attached teacher report.",
                    attachment_path=file_path,
                )
            finally:
                try:
                    os.remove(file_path)
                except OSError:
                    logger.error("Failed to delete temporary report file.")
            return {"message": "Teacher report saved and sent via email."}
        except Exception as exc:
            logger.error(f"Report generation error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @router.post("/profile/delete/")
    async def admin_delete_user_account(
        target_email: str = Form(...),
        admin_secret_input: str = Form(...),
        current_role: str = Depends(get_current_role),
    ):
        if not current_role or current_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden. Only administrators can delete user accounts.",
            )
        admin_secret = get_admin_secret("admin_secret")
        if not admin_secret or admin_secret_input != admin_secret:
            raise HTTPException(
                status_code=403,
                detail="Invalid administrator secret provided.",
            )

        try:
            message = admin_service.delete_user_account(target_email)
            return {
                "message": message
            }
        except UserAccountNotFound:
            raise HTTPException(
                status_code=404,
                detail=f"User account linked to '{target_email}' not found.",
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    return router
