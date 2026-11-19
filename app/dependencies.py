"""Shared request helpers: session getters and the cronjob secret check."""
import os
import logging
from fastapi import HTTPException, Request, Depends
from sqlalchemy.sql import select

from app.database import SessionLocal
from app.models import TeacherList

logger = logging.getLogger(__name__)

def get_current_id(request: Request):
    return request.session.get("user_id", None)

def get_current_role(request: Request):
    return request.session.get("user_role", None)

def get_current_email(request: Request):
    return request.session.get("user_email", None)

def get_index_cookie(index: str, request: Request):
    return request.session.get(index, None)

def store_my_cookies(request: Request, id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(TeacherList.regUserID == id)
        result = db.execute(query)
        teacher_data = result.fetchone()
        if teacher_data:
            name, state, county, district, school = teacher_data[0].name, teacher_data[0].state, teacher_data[0].county, teacher_data[0].district, teacher_data[0].school
            request.session["state"] = state
            request.session["county"] = county
            request.session["district"] = district
            request.session["school"] = school
            request.session["teacher"] = name
        else:
            raise HTTPException(status_code=404, detail="Your account does not have a database listing")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

def verify_cronjob_request(request: Request):
    secret = request.headers.get("x-secret-key")
    if not secret or secret != os.getenv("INTERNAL_JOB_SECRET"):
        raise HTTPException(status_code=403, detail="Forbidden")