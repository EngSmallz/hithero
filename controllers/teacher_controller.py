from fastapi import APIRouter, Form, Request, Depends, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from config import get_db
from services.teacher_service import TeacherService
from dependencies import get_current_user_id, get_current_user_role, get_current_user_email
from utils.session import get_session_value, set_session_values

router = APIRouter(prefix="/teacher", tags=["teachers"])

@router.post("/create_profile/")
async def create_teacher_profile(
    request: Request,
    name: str = Form(...),
    state: str = Form(...),
    county: str = Form(...),
    district: str = Form(...),
    school: str = Form(...),
    aboutMe: str = Form(...),
    wishlist: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    user_role: str = Depends(get_current_user_role),
    user_email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    teacher_data = {
        "name": name,
        "state": state,
        "county": county,
        "district": district,
        "school": school,
        "aboutMe": aboutMe,
        "wishlist": wishlist
    }
    result = teacher_service.create_teacher_profile(
        user_id, user_role, user_email, teacher_data
    )
    return result

@router.get("/random/")
async def get_random_teacher(
    request: Request,
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    teacher_data = teacher_service.get_random_teacher()
    
    # Set session cookies
    set_session_values(request, {
        "state": teacher_data["state"],
        "county": teacher_data["county"],
        "district": teacher_data["district"],
        "school": teacher_data["school"],
        "teacher": teacher_data["name"]
    })
    
    return teacher_data

@router.get("/info/")
async def get_teacher_info(
    request: Request,
    db: Session = Depends(get_db)
):
    state = get_session_value(request, 'state')
    county = get_session_value(request, 'county')
    district = get_session_value(request, 'district')
    school = get_session_value(request, 'school')
    name = get_session_value(request, 'teacher')
    
    teacher_service = TeacherService(db)
    return teacher_service.get_teacher_info_by_session(
        state, county, district, school, name
    )

@router.get("/myinfo/")
async def get_my_info(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    teacher_data = teacher_service.get_my_teacher_info(user_id)
    
    # Set session values
    set_session_values(request, teacher_data)
    
    return teacher_data

@router.get("/{url_id}")
async def get_teacher_by_url(
    url_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    try:
        teacher_data = teacher_service.get_teacher_by_url_id(url_id)
        set_session_values(request, teacher_data)
        return RedirectResponse(url="/pages/teacher.html")
    except:
        return RedirectResponse(url="/pages/404.html")

@router.post("/update_info/")
async def update_info(
    aboutMe: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    return teacher_service.update_teacher_info(user_id, aboutMe)

@router.post("/update_school/")
async def update_school(
    state: str = Form(...),
    county: str = Form(...),
    district: str = Form(...),
    school: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    school_data = {
        "state": state,
        "county": county,
        "district": district,
        "school": school
    }
    return teacher_service.update_teacher_school(user_id, school_data)

@router.post("/update_name/")
async def update_name(
    teacher: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    return teacher_service.update_teacher_name(user_id, teacher)

@router.post("/update_wishlist/")
async def update_wishlist(
    wishlist: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    return teacher_service.update_wishlist(user_id, wishlist)

@router.post("/update_url_id/")
async def update_url_id(
    url_id: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    teacher_service = TeacherService(db)
    return teacher_service.update_url_id(user_id, url_id)

@router.post("/update_image/")
async def update_image(
    request: Request,
    image: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    state = get_session_value(request, 'state')
    county = get_session_value(request, 'county')
    district = get_session_value(request, 'district')
    school = get_session_value(request, 'school')
    name = get_session_value(request, 'teacher')
    
    teacher_service = TeacherService(db)
    return teacher_service.update_teacher_image(
        image, state, county, district, school, name
    )

@router.get("/check_access/")
async def check_access(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    user_role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db)
):
    if user_role != 'teacher':
        raise HTTPException(status_code=403, detail="No access")
    
    state = get_session_value(request, 'state')
    county = get_session_value(request, 'county')
    district = get_session_value(request, 'district')
    school = get_session_value(request, 'school')
    name = get_session_value(request, 'teacher')
    
    teacher_service = TeacherService(db)
    has_access = teacher_service.check_teacher_access(
        user_id, state, county, district, school, name
    )
    
    if not has_access:
        raise HTTPException(status_code=403, detail="No access")
    
    return {"status": "success", "message": "Access granted"}

@router.get("/url/")
async def get_teacher_url(
    request: Request,
    db: Session = Depends(get_db)
):
    state = get_session_value(request, 'state')
    county = get_session_value(request, 'county')
    district = get_session_value(request, 'district')
    school = get_session_value(request, 'school')
    name = get_session_value(request, 'teacher')
    
    teacher_service = TeacherService(db)
    return teacher_service.get_teacher_url(
        state, county, district, school, name
    )