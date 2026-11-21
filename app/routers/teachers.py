"""Teacher routes: creating and editing profiles, the image upload, and public teacher pages."""
import base64
import logging
import re
import secrets
import puremagic
from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import String, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, cast, insert, update

from app.config import MAX_FILE_SIZE
from app.database import SessionLocal
from app.dependencies import get_current_email, get_current_id, get_current_role, get_index_cookie
from app.models import RegisteredUsers, TeacherList
from app.services.teachers import fetch_random_teacher

logger = logging.getLogger(__name__)
router = APIRouter()

##this api allows a logged in user to create an item in the table teacher_list in the hithero database if they have not created a user already
@router.post("/profile/create_teacher_profile/")
async def create_teacher_profile(request: Request, name: str = Form(...), state: str = Form(...), county: str = Form(...), district: str = Form(...), school: str = Form(...), aboutMe: str = Form(...), wishlist: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            query = select(RegisteredUsers.createCount).where(RegisteredUsers.id == id)
            result = db.execute(query)
            create_count = result.scalar()
            if create_count == 0 or role == 'admin':
                aa_link = wishlist + "&tag=h0mer00mher0-20" 
                email = get_current_email(request)
                first_part_email = email.split('@')[0]
                random_number = secrets.randbelow(9999)
                auto_url_id = f"{first_part_email}{random_number}"
                while db.execute(select(TeacherList).where(cast(TeacherList.url_id, String) == cast(auto_url_id, String))).first():
                    random_number = secrets.randbelow(9999)
                    auto_url_id = f"{first_part_email}{random_number}"

                insert_query = insert(TeacherList).values(
                    name=name,
                    state=state,
                    county=county,
                    district=district,
                    school=school,
                    regUserID=id,
                    about_me=aboutMe,
                    wishlist_url=aa_link,
                    url_id=auto_url_id
                )
                db.execute(insert_query)
                update_query = update(RegisteredUsers).where(RegisteredUsers.id == id).values(createCount=RegisteredUsers.createCount + 1)
                db.execute(update_query)
                db.commit()
                return {"message": "Teacher created successfully", "role": role}
            else:
                return {"message": "Unable to create new profile. Profile already created."}
        else:
            return {"message": "No user logged in."}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api gets a random teacher from the list teacher_list in the hithero data base

@router.get("/api/random_teacher/")
async def get_random_teacher(request: Request):
    try:
        teacher = fetch_random_teacher()
        if not teacher:
            raise HTTPException(status_code=404, detail="No teachers found in the database")
        if teacher.image_data:
            image_data = base64.b64encode(teacher.image_data).decode('utf-8')
        else:
            image_data = None
        data = {
            "name": teacher.name,
            "state": teacher.state,
            "county": teacher.county,
            "district": teacher.district,
            "school": teacher.school,
            "image_data": image_data
        }
        if hasattr(request, "session"):
            request.session["state"] = data["state"]
            request.session["county"] = data["county"]
            request.session["district"] = data["district"]
            request.session["school"] = data["school"]
            request.session["teacher"] = data["name"]
        return data
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")

###api gets a teacher data from teacher_list table
@router.get("/api/get_teacher_info/")
async def get_teacher_info(request: Request):
    db = SessionLocal()
    try:
        state = get_index_cookie('state', request)
        county = get_index_cookie('county', request)
        district = get_index_cookie('district', request)
        school = get_index_cookie('school', request)
        name = get_index_cookie('teacher', request)
        query = select(TeacherList).where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county) &
            (cast(TeacherList.district, String) == district) &
            (cast(TeacherList.school, String) == school) &
            (cast(TeacherList.name, String) == name)
        )
        result = db.execute(query)
        teacher_info = result.fetchone()
        if teacher_info:
            if teacher_info[0].image_data:
                image_data = base64.b64encode(teacher_info[0].image_data).decode('utf-8')
            else:
                image_data = None
            data = {
                "state": teacher_info[0].state,
                "county": teacher_info[0].county,
                "district": teacher_info[0].district,
                "school": teacher_info[0].school,
                "name": teacher_info[0].name,
                "wishlist_url": teacher_info[0].wishlist_url,
                "about_me": teacher_info[0].about_me,
                "image_data": image_data
            }
            return data
        else:
            raise HTTPException(status_code=404, detail="Teacher not found")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api that updates about me info
@router.post("/profile/update_info/")
async def update_info(request: Request, aboutMe: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(about_me=aboutMe)
            db.execute(update_query)
            db.commit()
            return {"message": "Info updated."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api that updates school
@router.post("/profile/update_teacher_school/")
async def update_teacher_school(
    request: Request,
    state: str = Form(...),
    county: str = Form(...),
    district: str = Form(...),
    school: str = Form(...),
    id: int = Depends(get_current_id),
    role: str = Depends(get_current_role)
):
    db: Session = SessionLocal()
    try:
        if role:
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(
                state=state,
                county=county,
                district=district,
                school=school
            )
            db.execute(update_query)
            db.commit()
            return JSONResponse(content={"message": "School information updated successfully."})
        else:
            raise HTTPException(status_code=403, detail="Permission denied. Not logged in.")
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api that updates name
@router.post("/profile/update_teacher_name/")
async def update_teacher_name(request: Request, teacher: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(name=teacher)
            db.execute(update_query)
            db.commit()
            return {"message": "Name updated."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except Exception as e:
        db.rollback()
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api to update wishlist
@router.post("/profile/update_wishlist/")
async def update_wishlist(request: Request, wishlist: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            aa_link = wishlist + "&tag=h0mer00mher0-20"
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(wishlist_url=aa_link)
            db.execute(update_query)
            db.commit()
            return {"message": "Wishlist updated."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

#api that update the url of a teachers page
@router.post("/profile/update_url_id/")
async def update_url_id(request: Request, url_id: str = Form(...), id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role:
            if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', url_id):
                raise HTTPException(status_code=400, detail="URL ID may only contain letters, numbers, hyphens, and underscores (3–50 characters).")
            existing_teacher = db.query(TeacherList).where(cast(TeacherList.url_id, String) == cast(url_id, String)).first()
            if existing_teacher:
                raise HTTPException(status_code=409, detail="URL ID already in use.")
            update_query = update(TeacherList).where(TeacherList.regUserID == id).values(url_id=url_id)
            db.execute(update_query)
            db.commit()
            return {"message": "URL ID updated successfully."}
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

###api used to update the logged in users teacher page image
@router.post("/profile/update_teacher_image/")
async def edit_teacher_image(request: Request, role: str = Depends(get_current_role), image: UploadFile = Form(...), id: int = Depends(get_current_id)):
    db: Session = SessionLocal()
    try:
        if image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds the allowed limit")
        
        # Read bytes once, then use for both magic check and DB storage
        image_bytes = await image.read()
        
        # Validate by actual file signature, not client-supplied content_type
        ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        
        # puremagic has no magic_buffer (no release ever had it), so every upload
        # raised AttributeError and returned 500. magic_string takes bytes and
        # returns matches best first; empty or unrecognised input raises.
        try:
            results = puremagic.magic_string(image_bytes)
        except (puremagic.PureError, ValueError):
            results = []
        detected_type = results[0].mime_type if results else None

        if detected_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
        
        if role:
            update_query = update(TeacherList).values(image_data=image_bytes).where(
                TeacherList.regUserID == id
            )
            db.execute(update_query)
            db.commit()
            return {"message": "Information updated."}
        else:
            return {"message": "Permission denied."}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

##api gets your page based on the id in reg_users and and regUserID in teacher_list
@router.get("/profile/myinfo/")
async def get_myinfo(request: Request, id: int = Depends(get_current_id)):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(TeacherList.regUserID == id)
        result = db.execute(query)
        teacher_data = result.fetchone()
        if teacher_data:
            state = teacher_data[0].state
            county = teacher_data[0].county
            district = teacher_data[0].district
            school = teacher_data[0].school
            name = teacher_data[0].name
            request.session["state"] = state
            request.session["county"] = county
            request.session["district"] = district
            request.session["school"] = school
            request.session["teacher"] = name
            return {"state": state, "county": county, "district": district, "school": school, "teacher": name}
        else:
            return {"message": "Your account does not have a database listing"}
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

#api to check if a user has edit acces to teacher page
@router.get("/api/check_access_teacher/")
async def check_access_teacher(request: Request, id: int = Depends(get_current_id), role: str = Depends(get_current_role)):
    db = SessionLocal()
    try:
        if role == 'teacher':
            state = get_index_cookie('state', request)
            county = get_index_cookie('county', request)
            district = get_index_cookie('district', request)
            school = get_index_cookie('school', request)
            name = get_index_cookie('teacher', request)
            query = select(TeacherList.regUserID).where(
                (cast(TeacherList.state, String) == state) &
                (cast(TeacherList.county, String) == county) &
                (cast(TeacherList.district, String) == district) &
                (cast(TeacherList.school, String) == school) &
                (cast(TeacherList.name, String) == name)
            )
            result = db.execute(query)
            teacher_data = result.scalar()
            if teacher_data == id:
                return {"status": "success", "message": "Access granted"}
        raise HTTPException(status_code=403, detail="No access")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

#api that gets today's Teacher of the Day (whoever has the most recent last_TOD)
@router.get("/api/teacher_of_the_day")
async def get_teacher_of_the_day(request: Request):
    db = SessionLocal()
    try:
        query = (
            select(TeacherList)
            .where(TeacherList.last_TOD.isnot(None))
            .order_by(desc(TeacherList.last_TOD))
            .limit(1)
        )
        result = db.execute(query)
        row = result.fetchone()
        if row:
            data = row[0]
            if data.image_data:
                image_data = base64.b64encode(data.image_data).decode('utf-8')
            else:
                image_data = None
            request.session['state'] = data.state
            request.session['county'] = data.county
            if data.district:
                request.session['district'] = data.district
            if data.school:
                request.session['school'] = data.school
                request.session['teacher'] = data.name
            data_dict = {
                "state": data.state,
                "county": data.county,
                "district": data.district,
                "school": data.school,
                "name": data.name,
                "image_data": image_data,
                "url_id": data.url_id
            }
            return data_dict
        else:
            raise HTTPException(status_code=404, detail="Teacher of the Day not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

###api to get a link for the url to your page to share
@router.get("/api/teacher_url/")
async def get_teacher_url(request: Request):
    db = SessionLocal()
    try:
        state = get_index_cookie('state', request)
        county = get_index_cookie('county', request)
        district = get_index_cookie('district', request)
        school = get_index_cookie('school', request)
        name = get_index_cookie('teacher', request)
        query = select(TeacherList.url_id).where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county) &
            (cast(TeacherList.district, String) == district) &
            (cast(TeacherList.school, String) == school) &
            (cast(TeacherList.name, String) == name)
        )
        result = db.execute(query)
        token = result.fetchone()
        if not token:
            raise HTTPException(status_code=404, detail="No matching teacher found")
        url = "www.HelpTeachers.net/teacher/" + token[0]
        return {"url": url}  # Return as JSON
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")

##this api gets the token, gets the data, sets the data, then redirects
@router.get("/teacher/{url_id}")
async def get_teacher_info(url_id: str, request: Request):
    db = SessionLocal()
    try:
        query = select(TeacherList).where(cast(TeacherList.url_id, String) == url_id)
        result = db.execute(query)
        teacher_info = result.fetchone()
        if not teacher_info:
            return RedirectResponse(url="/pages/404.html")
        request.session['state'] = teacher_info[0].state
        request.session['county'] = teacher_info[0].county
        request.session['district'] = teacher_info[0].district
        request.session['school'] = teacher_info[0].school
        request.session['teacher'] = teacher_info[0].name

        return RedirectResponse(url="/pages/teacher.html")
    except Exception as e:
        return RedirectResponse(url="/pages/404.html")