from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse

from backend.repositories.teachers import TeacherDirectoryRepository
from backend.services.teacher_directory import TeacherDirectoryService


def create_teacher_router(
    *,
    session_factory,
    school_model,
    teacher_model,
    directory_response_model,
    profile_response_model,
):
    router = APIRouter()
    directory_service = TeacherDirectoryService(
        TeacherDirectoryRepository(
            session_factory=session_factory,
            school_model=school_model,
            teacher_model=teacher_model,
        )
    )

    @router.get("/api/get_states/")
    async def get_states():
        return directory_service.get_school_states()

    @router.get("/api/get_counties/{state}")
    async def get_counties(state: str):
        return directory_service.get_school_counties(state)

    @router.get("/api/get_districts/{state}/{county}")
    async def get_districts(state: str, county: str):
        return directory_service.get_school_districts(state, county)

    @router.get("/api/get_schools/{state}/{county}/{district}")
    async def get_schools(state: str, county: str, district: str):
        return directory_service.get_school_names(state, county, district)

    @router.get("/api/index_states/")
    async def index_states():
        return directory_service.get_index_states()

    @router.get("/api/index_counties/{state}")
    async def index_counties(state: str):
        return directory_service.get_index_counties(state)

    @router.get("/api/index_districts/{state}/{county}")
    async def index_districts(state: str, county: str):
        return directory_service.get_index_districts(state, county)

    @router.get("/api/index_schools/{state}/{county}/{district}")
    async def index_schools(state: str, county: str, district: str):
        return directory_service.get_index_schools(state, county, district)

    @router.get("/api/teachers/", response_model=directory_response_model)
    async def list_teachers(
        state: Optional[str] = None,
        county: Optional[str] = None,
        district: Optional[str] = None,
        school: Optional[str] = None,
        page: int = 1,
        page_size: int = 24,
    ):
        return directory_service.build_directory_response(
            state=state,
            county=county,
            district=district,
            school=school,
            page=page,
            page_size=page_size,
        )

    @router.get("/api/teacher/{url_id}/", response_model=profile_response_model)
    async def get_public_teacher_profile(url_id: str):
        profile = directory_service.get_public_teacher_profile(url_id)
        if profile is None:
            return JSONResponse(status_code=404, content={"detail": "Teacher not found"})
        return profile

    @router.post("/api/index_teachers/")
    async def index_teachers(
        state: str = Form(...),
        county: str = Form(None),
        district: str = Form(None),
        school: str = Form(None),
    ):
        teachers = directory_service.find_index_teachers(
            state=state,
            county=county,
            district=district,
            school=school,
        )
        if teachers is None:
            raise HTTPException(
                status_code=404,
                detail="No teachers found with the given criteria.",
            )
        return teachers

    return router
