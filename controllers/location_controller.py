from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from config import get_db
from repositories.school_repository import SchoolRepository
from repositories.teacher_repository import TeacherRepository

router = APIRouter(prefix="/location", tags=["locations"])

@router.get("/states/")
async def get_states(db: Session = Depends(get_db)):
    school_repo = SchoolRepository(db)
    return school_repo.get_distinct_states()

@router.get("/counties/{state}")
async def get_counties(state: str, db: Session = Depends(get_db)):
    school_repo = SchoolRepository(db)
    return school_repo.get_distinct_counties(state)

@router.get("/districts/{state}/{county}")
async def get_districts(
    state: str,
    county: str,
    db: Session = Depends(get_db)
):
    school_repo = SchoolRepository(db)
    return school_repo.get_distinct_districts(state, county)

@router.get("/schools/{state}/{county}/{district}")
async def get_schools(
    state: str,
    county: str,
    district: str,
    db: Session = Depends(get_db)
):
    school_repo = SchoolRepository(db)
    return school_repo.get_distinct_schools(state, county, district)

# Index endpoints for teacher locations
@router.get("/index/states/")
async def index_states(db: Session = Depends(get_db)):
    teacher_repo = TeacherRepository(db)
    return teacher_repo.get_distinct_states()

@router.get("/index/counties/{state}")
async def index_counties(state: str, db: Session = Depends(get_db)):
    teacher_repo = TeacherRepository(db)
    return teacher_repo.get_distinct_counties(state)

@router.get("/index/districts/{state}/{county}")
async def index_districts(
    state: str,
    county: str,
    db: Session = Depends(get_db)
):
    teacher_repo = TeacherRepository(db)
    return teacher_repo.get_distinct_districts(state, county)

@router.get("/index/schools/{state}/{county}/{district}")
async def index_schools(
    state: str,
    county: str,
    district: str,
    db: Session = Depends(get_db)
):
    teacher_repo = TeacherRepository(db)
    return teacher_repo.get_distinct_schools(state, county, district)

@router.post("/index/teachers/")
async def index_teachers(
    state: str = Form(...),
    county: str = Form(None),
    district: str = Form(None),
    school: str = Form(None),
    db: Session = Depends(get_db)
):
    teacher_repo = TeacherRepository(db)
    teachers = teacher_repo.get_teachers_by_location(
        state, county, district, school
    )
    
    if not teachers:
        raise HTTPException(
            status_code=404,
            detail="No teachers found"
        )
    
    return [{"name": t.name, "url_id": t.url_id} for t in teachers]