"""Admin routes: teacher PDF report, deleting any user account, and creating admin accounts."""
import io
import logging
import os
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from passlib.hash import sha256_crypt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from sqlalchemy import String
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, cast, delete

from app.database import SessionLocal
from app.dependencies import get_current_role
from app.limiter import limiter
from app.models import NewUsers, RegisteredUsers, TeacherList

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/admin/generate_teacher_report/")
async def generate_teacher_report(state: str = Form(...), county: str = Form(None), district: str = Form(None), school: str = Form(None), role: str = Depends(get_current_role)):
    if role != 'admin':
        raise HTTPException(status_code=403, detail="Access denied: Only administrators can generate reports.")
    db: Session = SessionLocal()
    try:
        # Step 1: Dynamically filter TeacherList based on provided fields (excluding regUserID)
        query = select(
            TeacherList.name, TeacherList.school, TeacherList.regUserID
        ).where(cast(TeacherList.state, String) == state)

        if county:
            query = query.where(cast(TeacherList.county, String) == county)
        if district:
            query = query.where(cast(TeacherList.district, String) == district)
        if school:
            query = query.where(cast(TeacherList.school, String) == school)

        teachers = db.execute(query).fetchall()

        if not teachers:
            raise HTTPException(status_code=404, detail="No teachers found with the specified criteria.")

        # Step 2: Fetch email and phone from RegisteredUsers using regUserID
        reg_user_ids = [teacher.regUserID for teacher in teachers]
        user_query = select(
            RegisteredUsers.id,
            RegisteredUsers.email,
            RegisteredUsers.phone_number).where(RegisteredUsers.id.in_(reg_user_ids))
        users = db.execute(user_query).fetchall()

        # Step 3: Map teachers to their corresponding user data (email and phone)
        user_dict = {user.id: {"email": user.email, "phone": user.phone_number} for user in users}

        table_data = [["Name", "School", "Email", "Phone"]]
        for teacher in teachers:
            table_data.append([
                teacher.name or "",
                teacher.school or "",
                user_dict.get(teacher.regUserID, {}).get('email', 'N/A'),
                user_dict.get(teacher.regUserID, {}).get('phone', 'N/A'),
            ])

        # Step 4: Build the PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("Teacher Report", styles['Title']), Spacer(1, 12)]

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        doc.build(story)
        buffer.seek(0)

        # Step 5: Stream the PDF back to the browser as a download
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=teacher_report.pdf"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        db.close()

@router.post("/profile/delete/")
async def admin_delete_user_account(target_email: str = Form(...), admin_secret_input: str = Form(...),current_role: str = Depends(get_current_role)):
    """
    Allows an authenticated 'admin' user to delete *any* user account 
    by providing the target user's email and a secret key via form submission.
    Deletes the associated teacher entry and the registered user account.
    """
    db: Session = SessionLocal()
    
    # 1. ROLE CHECK: Ensure the current user is an admin
    if not current_role or current_role != 'admin':
        raise HTTPException(status_code=403, detail="Forbidden. Only administrators can delete user accounts.")

    # 2. SECRET CHECK: Ensure the provided secret matches the server configuration
    # The user-provided prompt suggests checking os.getenv("DATABASE_SERVER")
    ADMIN_SECRET = os.getenv("admin_secret")
    
    if not ADMIN_SECRET or admin_secret_input != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid administrator secret provided.")

    try:
        # 3. FIND THE TARGET USER ID
        # Select the ID of the user to be deleted based on the target email.
        user_id_query = select(RegisteredUsers.id).where(
            cast(RegisteredUsers.email, String) == cast(target_email, String)
        )
        user_id_result = db.execute(user_id_query).fetchone()

        if not user_id_result:
            raise HTTPException(status_code=404, detail=f"User account linked to '{target_email}' not found.")

        target_user_id = user_id_result[0]

        # 4. DELETE FROM teacher_list
        # Delete the entry in the teacher_list linked to this user ID (regUserID).
        delete_teacher_query = delete(TeacherList).where(
            TeacherList.regUserID == target_user_id
        )
        teacher_result = db.execute(delete_teacher_query)

        # 5. DELETE FROM registered_users
        # Delete the user account itself using the email.
        delete_user_query = delete(RegisteredUsers).where(
            cast(RegisteredUsers.email, String) == cast(target_email, String)
        )
        user_result = db.execute(delete_user_query)
        db.commit()
        return {"message": f"Successfully deleted account and associated data for target user: {target_email}."}

    except HTTPException as h:
        raise h
    except Exception as e:
        db.rollback()
        print(f"Error during administrative account deletion for {target_email}: {str(e)}")
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Internal Server Error")
    finally:
        db.close()

@router.post("/admin/create_admin/")
@limiter.limit("5/minute")
async def create_admin_account(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    admin_secret_input: str = Form(...),
    current_role: str = Depends(get_current_role)
):
    """
    Allows an authenticated 'admin' user, who also supplies the server's admin
    secret, to create a brand new admin account directly in registered_users.
    Only email, password, and role are stored; id is auto-assigned by the DB.
    """
    # 1. ROLE CHECK: Only an existing admin may create another admin
    if not current_role or current_role != 'admin':
        raise HTTPException(status_code=403, detail="Forbidden. Only administrators can create admin accounts.")

    # 2. SECRET CHECK: Same server secret used for other sensitive admin actions
    ADMIN_SECRET = os.getenv("admin_secret")
    if not ADMIN_SECRET or admin_secret_input != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid administrator secret provided.")

    # 3. BASIC VALIDATION
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    db: Session = SessionLocal()
    try:
        # 4. Make sure this email isn't already in use, in either table
        existing_registered = db.execute(
            select(RegisteredUsers.id).where(cast(RegisteredUsers.email, String) == cast(email, String))
        ).fetchone()
        existing_pending = db.execute(
            select(NewUsers.id).where(cast(NewUsers.email, String) == cast(email, String))
        ).fetchone()
        if existing_registered or existing_pending:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")

        # 5. Create the admin account directly in registered_users (id auto-assigned by the DB)
        hashed_password = sha256_crypt.hash(password)
        new_admin = RegisteredUsers(
            email=email,
            password=hashed_password,
            role='admin',
            createCount=0
        )
        db.add(new_admin)
        db.commit()
        return {"message": f"Admin account created successfully for {email}."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin account: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()