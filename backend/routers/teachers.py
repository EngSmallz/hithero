from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import String, cast, func, select

from backend.services.teachers import serialize_teacher_profile, serialize_teacher_summary


def _clean_optional_filter(value: Optional[str]):
    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


def _sorted_distinct_values(db, column, *conditions):
    query = select(cast(column, String)).distinct()
    for condition in conditions:
        if condition is not None:
            query = query.where(condition)

    values = db.execute(query).scalars().all()
    return sorted({value for value in values if value})


def create_teacher_router(
    *,
    session_factory,
    school_model,
    teacher_model,
    directory_response_model,
    profile_response_model,
):
    router = APIRouter()

    def build_directory_response(
        db,
        state: Optional[str] = None,
        county: Optional[str] = None,
        district: Optional[str] = None,
        school: Optional[str] = None,
        page: int = 1,
        page_size: int = 24,
    ):
        state = _clean_optional_filter(state)
        county = _clean_optional_filter(county)
        district = _clean_optional_filter(district)
        school = _clean_optional_filter(school)
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        conditions = [
            teacher_model.name.is_not(None),
            teacher_model.url_id.is_not(None),
            cast(teacher_model.url_id, String) != "",
        ]
        if state:
            conditions.append(cast(teacher_model.state, String) == state)
        if county:
            conditions.append(cast(teacher_model.county, String) == county)
        if district:
            conditions.append(cast(teacher_model.district, String) == district)
        if school:
            conditions.append(cast(teacher_model.school, String) == school)

        total = db.execute(
            select(func.count()).select_from(teacher_model).where(*conditions)
        ).scalar_one()
        total_pages = (total + page_size - 1) // page_size if total else 0
        if total_pages:
            page = min(page, total_pages)
        offset = (page - 1) * page_size

        teacher_query = (
            select(teacher_model)
            .where(*conditions)
            .order_by(cast(teacher_model.name, String))
            .offset(offset)
            .limit(page_size)
        )

        teachers = db.execute(teacher_query).scalars().all()

        county_conditions = [cast(teacher_model.state, String) == state] if state else []
        district_conditions = county_conditions + (
            [cast(teacher_model.county, String) == county] if county else []
        )
        school_conditions = district_conditions + (
            [cast(teacher_model.district, String) == district] if district else []
        )

        return {
            "teachers": [serialize_teacher_summary(teacher) for teacher in teachers],
            "filters": {
                "states": _sorted_distinct_values(db, teacher_model.state),
                "counties": _sorted_distinct_values(
                    db, teacher_model.county, *county_conditions
                ),
                "districts": _sorted_distinct_values(
                    db, teacher_model.district, *district_conditions
                ),
                "schools": _sorted_distinct_values(
                    db, teacher_model.school, *school_conditions
                ),
            },
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "applied_filters": {
                "state": state,
                "county": county,
                "district": district,
                "school": school,
            },
        }

    @router.get("/api/get_states/")
    async def get_states():
        db = session_factory()
        try:
            states = db.query(school_model.state).distinct().all()
            return sorted([state[0] for state in states])
        finally:
            db.close()

    @router.get("/api/get_counties/{state}")
    async def get_counties(state: str):
        db = session_factory()
        try:
            counties = db.execute(
                select(school_model.county)
                .distinct()
                .where(school_model.state == state)
            ).fetchall()
            if counties:
                return sorted([county[0] for county in counties])
            return {"message": f"No counties found for state: {state}"}
        finally:
            db.close()

    @router.get("/api/get_districts/{state}/{county}")
    async def get_districts(state: str, county: str):
        db = session_factory()
        try:
            districts = db.execute(
                select(school_model.district)
                .distinct()
                .where(
                    (school_model.state == state) & (school_model.county == county)
                )
            ).fetchall()
            if districts:
                return sorted([district[0] for district in districts])
            return {
                "message": f"No districts found for state: {state} and county: {county}"
            }
        finally:
            db.close()

    @router.get("/api/get_schools/{state}/{county}/{district}")
    async def get_schools(state: str, county: str, district: str):
        db = session_factory()
        try:
            schools = db.execute(
                select(school_model.school_name)
                .distinct()
                .where(
                    (school_model.state == state)
                    & (school_model.county == county)
                    & (school_model.district == district)
                )
            ).fetchall()
            if schools:
                return sorted([school[0] for school in schools])
            return {
                "message": (
                    f"No schools found for state: {state}, county: {county}, "
                    f"and district: {district}"
                )
            }
        finally:
            db.close()

    @router.get("/api/index_states/")
    async def index_states():
        db = session_factory()
        try:
            states = db.query(cast(teacher_model.state, String)).distinct().all()
            return sorted([state[0] for state in states])
        finally:
            db.close()

    @router.get("/api/index_counties/{state}")
    async def index_counties(state: str):
        db = session_factory()
        try:
            counties = db.execute(
                select(cast(teacher_model.county, String))
                .distinct()
                .where(cast(teacher_model.state, String) == state)
            ).fetchall()
            if counties:
                return sorted([county[0] for county in counties])
            return {"message": f"No counties found for state: {state}"}
        finally:
            db.close()

    @router.get("/api/index_districts/{state}/{county}")
    async def index_districts(state: str, county: str):
        db = session_factory()
        try:
            districts = db.execute(
                select(cast(teacher_model.district, String))
                .distinct()
                .where(
                    (cast(teacher_model.state, String) == state)
                    & (cast(teacher_model.county, String) == county)
                )
            ).fetchall()
            if districts:
                return sorted([district[0] for district in districts])
            return {
                "message": f"No districts found for state: {state} and county: {county}"
            }
        finally:
            db.close()

    @router.get("/api/index_schools/{state}/{county}/{district}")
    async def index_schools(state: str, county: str, district: str):
        db = session_factory()
        try:
            schools = db.execute(
                select(cast(teacher_model.school, String))
                .distinct()
                .where(
                    (cast(teacher_model.state, String) == state)
                    & (cast(teacher_model.county, String) == county)
                    & (cast(teacher_model.district, String) == district)
                )
            ).fetchall()
            if schools:
                return sorted([school[0] for school in schools])
            return {
                "message": (
                    f"No schools found for state: {state}, county: {county}, "
                    f"and district: {district}"
                )
            }
        finally:
            db.close()

    @router.get("/api/teachers/", response_model=directory_response_model)
    async def list_teachers(
        state: Optional[str] = None,
        county: Optional[str] = None,
        district: Optional[str] = None,
        school: Optional[str] = None,
        page: int = 1,
        page_size: int = 24,
    ):
        db = session_factory()
        try:
            return build_directory_response(
                db,
                state=state,
                county=county,
                district=district,
                school=school,
                page=page,
                page_size=page_size,
            )
        finally:
            db.close()

    @router.get("/api/teacher/{url_id}/", response_model=profile_response_model)
    async def get_public_teacher_profile(url_id: str):
        db = session_factory()
        try:
            teacher = db.execute(
                select(teacher_model).where(
                    cast(teacher_model.url_id, String) == url_id
                )
            ).scalar_one_or_none()

            if not teacher:
                return JSONResponse(
                    status_code=404, content={"detail": "Teacher not found"}
                )

            return serialize_teacher_profile(teacher)
        finally:
            db.close()

    @router.post("/api/index_teachers/")
    async def index_teachers(
        state: str = Form(...),
        county: str = Form(None),
        district: str = Form(None),
        school: str = Form(None),
    ):
        db = session_factory()
        try:
            query = select(teacher_model.name, teacher_model.url_id).where(
                cast(teacher_model.state, String) == state
            )

            if county:
                query = query.where(cast(teacher_model.county, String) == county)
            if district:
                query = query.where(cast(teacher_model.district, String) == district)
            if school:
                query = query.where(cast(teacher_model.school, String) == school)

            teachers = db.execute(query).fetchall()
            if teachers:
                return [
                    {"name": teacher.name, "url_id": teacher.url_id}
                    for teacher in teachers
                ]
            raise HTTPException(
                status_code=404,
                detail="No teachers found with the given criteria.",
            )
        finally:
            db.close()

    return router
