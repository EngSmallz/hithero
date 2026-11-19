"""Location lookup routes: state/county/district/school dropdown data and the teacher index."""
from fastapi import APIRouter, Form, HTTPException
from sqlalchemy import String
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, cast

from app.database import SessionLocal
from app.models import School, TeacherList

router = APIRouter()

#api gets a list of states from statecoutny table
@router.get("/api/get_states/")
async def get_states():
    db = SessionLocal()
    try:
        states = db.query(School.state).distinct().all()
        return sorted([state[0] for state in states])
    finally:
        db.close()

#api gets the names of the counties in the desired state
@router.get("/api/get_counties/{state}")
async def get_counties(state: str):
    db = SessionLocal()
    try:
        query = select(School.county).distinct().where(School.state == state)
        result = db.execute(query)
        counties = result.fetchall()
        if counties:
            county_names = sorted([county[0] for county in counties])
            return county_names
        else:
            return {"message": f"No counties found for state: {state}"}
    finally:
        db.close()

#api gets the names of the school districts in the desired county and state
@router.get("/api/get_districts/{state}/{county}")
async def get_districts(state: str, county: str):
    db = SessionLocal()
    try:
        query = select(School.district).distinct().where((School.state == state) & (School.county == county))
        result = db.execute(query)
        districts = result.fetchall()
        if districts:
            district_names = sorted([district[0] for district in districts])
            return district_names
        else:
            return {"message": f"No districts found for state: {state} and county: {county}"}
    finally:
        db.close()

#api gets the names of the school in the desired district, coutny, and state
@router.get("/api/get_schools/{state}/{county}/{district}")
async def get_schools(state: str, county: str, district: str):
    db = SessionLocal()
    try:
        query = select(School.school_name).distinct().where((School.state == state) & (School.county == county) & (School.district == district))
        result = db.execute(query)
        schools = result.fetchall()
        if schools:
            school_names = sorted([school[0] for school in schools])
            return school_names
        else:
            return {"message": f"No schools found for state: {state}, county: {county}, and district: {district}"}
    finally:
        db.close()

#api gets a list of states from statecoutny table
@router.get("/api/index_states/")
async def index_states():
    db = SessionLocal()
    try:
        states = db.query(cast(TeacherList.state, String)).distinct().all()
        return sorted([state[0] for state in states])
    finally:
        db.close()

#api gets the names of the counties in the desired state
@router.get("/api/index_counties/{state}")
async def index_counties(state: str):
    db = SessionLocal()
    try:
        query = select(cast(TeacherList.county, String)).distinct().where(cast(TeacherList.state, String) == state)
        result = db.execute(query)
        counties = result.fetchall()
        if counties:
            county_names = sorted([county[0] for county in counties])
            return county_names
        else:
            return {"message": f"No counties found for state: {state}"}
    finally:
        db.close()

#api gets the names of the school districts in the desired county and state
@router.get("/api/index_districts/{state}/{county}")
async def index_districts(state: str, county: str):
    db = SessionLocal()
    try:
        query = select(cast(TeacherList.district, String)).distinct().where((cast(TeacherList.state, String) == state) & (cast(TeacherList.county, String) == county))
        result = db.execute(query)
        districts = result.fetchall()
        if districts:
            district_names = sorted([district[0] for district in districts])
            return district_names
        else:
            return {"message": f"No districts found for state: {state} and county: {county}"}
    finally:
        db.close()

#api gets the names of the school in the desired district, coutny, and state
@router.get("/api/index_schools/{state}/{county}/{district}")
async def index_schools(state: str, county: str, district: str):
    db = SessionLocal()
    try:
        query = select(cast(TeacherList.school, String)).distinct().where((cast(TeacherList.state, String) == state) & (cast(TeacherList.county, String) == county) & (cast(TeacherList.district, String) == district))       
        result = db.execute(query)
        schools = result.fetchall()
        if schools:
            school_names = sorted([school[0] for school in schools])
            return school_names
        else:
            return {"message": f"No schools found for state: {state}, county: {county}, and district: {district}"}
    finally:
        db.close()

###api gets the teachers and their url_id for the index
@router.post("/api/index_teachers/")
async def index_teachers(state: str = Form(...),county: str = Form(None),district: str = Form(None),school: str = Form(None)):
    db: Session = SessionLocal()
    try:
        query = select(TeacherList.name, TeacherList.url_id).where(
            (cast(TeacherList.state, String) == state)
        )

        if county:
            query = query.where(cast(TeacherList.county, String) == county)
        if district:
            query = query.where(cast(TeacherList.district, String) == district)
        if school:
            query = query.where(cast(TeacherList.school, String) == school)

        result = db.execute(query)
        teachers = result.fetchall()

        if teachers:
            return [{"name": teacher.name, "url_id": teacher.url_id} for teacher in teachers]
        else:
            raise HTTPException(
                status_code=404,
                detail="No teachers found with the given criteria."
            )
    finally:
        db.close()