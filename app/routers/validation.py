"""Validation routes: approving, listing, deleting, reporting, and marking new users as emailed."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import String
from sqlalchemy.sql import select, cast, delete, insert, update

from app.database import SessionLocal
from app.dependencies import get_current_id, get_current_role, get_index_cookie, store_my_cookies
from app.models import NewUsers, RegisteredUsers, TeacherList
from app.services.emailer import send_validation_email

logger = logging.getLogger(__name__)
router = APIRouter()

# Endpoint to move a user from new_users to registered_users and delete item in new_users
@router.post("/validation/validate_user/{user_email}")
async def move_user(user_email: str, role: str = Depends(get_current_role), request: Request = None):
    if role not in ('admin', 'teacher'):
        raise HTTPException(status_code=403, detail="Access denied.")
    db = SessionLocal()
    try:
        query = select(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
        result = db.execute(query)
        user = result.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in new_users")

        # Teachers can only validate users within their own district
        if role == 'teacher':
            id = get_current_id(request)
            teacher_record = db.execute(select(TeacherList).where(TeacherList.regUserID == id)).fetchone()
            if not teacher_record or (
                user[0].state != teacher_record[0].state or
                user[0].county != teacher_record[0].county or
                user[0].district != teacher_record[0].district
            ):
                raise HTTPException(status_code=403, detail="You can only validate teachers in your own district.")
        
        query = insert(RegisteredUsers).values(email=user[0].email, password=user[0].password, role=user[0].role, phone_number = user[0].phone_number)
        db.execute(query)
        delete_query = delete(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
        db.execute(delete_query)
        db.commit()
        send_validation_email(user[0].email)        
        return {"message": "User validated."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

#gets a list of unverified users to validate based on the role of the user
@router.get("/api/validation_list/")
async def validation_page(request: Request, role: str = Depends(get_current_role), id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        if role == "admin":
            query = select(NewUsers)
            result = db.execute(query)
            new_users = result.fetchall()
            return {"new_users": [{"name": user[0].name, "email": user[0].email, "state": user[0].state, "district": user[0].district, "school": user[0].school, "phone_number": user[0].phone_number, "report": user[0].report, "emailed": user[0].emailed} for user in new_users], "role": role}
        if role == 'teacher':
            store_my_cookies(request, id)
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            query = select(NewUsers).where(
                (cast(NewUsers.state, String) == state) &
                (cast(NewUsers.county, String) == county) &
                (cast(NewUsers.district, String) == district)
            )
            result = db.execute(query)
            new_users = result.fetchall()
            return {"new_users": [{"name": user[0].name, "email": user[0].email, "state": user[0].state, "district": user[0].district, "school": user[0].school, "phone_number": user[0].phone_number, "report": user[0].report, "emailed": user[0].emailed} for user in new_users], "role": role}
        else:
            raise HTTPException(status_code=403, detail="You don't have permission to access this page.")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")          
    finally:
        db.close()

# Endpoint to  users
@router.post("/validation/delete_user/{user_email}")
async def delete_user(user_email: str, role: str = Depends(get_current_role)):
    if role == 'admin':
        db = SessionLocal()
        try:
            query = select(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
            result = db.execute(query)
            user = result.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found in new_users")
            delete_query = delete(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String))
            db.execute(delete_query)
            db.commit()
            return {"message": "User deleted successfully."}
        except Exception as e:
            db.rollback()
            logger.error(f"Internal Server Error: {str(e)}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()
    else:
        raise HTTPException(status_code=403, detail=f"No permission to to action.")

# Function to report a user in validation
@router.post("/validation/report_user/{user_email}")
async def report_user(user_email: str, role: str = Depends(get_current_role)):
    if role not in ('admin', 'teacher'):
        raise HTTPException(status_code=403, detail="Access denied.")
    db = SessionLocal()
    try:
        update_query = update(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String)).values(report=1)
        db.execute(update_query)
        db.commit()
        return {"message": "User reported."}
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

# Endpoint to mark that a new users has been emailed
@router.post("/validation/emailed_user/{user_email}")
async def emailed_user(user_email: str, role: str = Depends(get_current_role)):
    if role not in ('admin', 'teacher'):
        raise HTTPException(status_code=403, detail="Access denied.")
    db = SessionLocal()
    try:
        update_query = update(NewUsers).where(cast(NewUsers.email, String) == cast(user_email, String)).values(emailed=1)
        db.execute(update_query)
        db.commit()
        return {"message": "User emailed."}
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()