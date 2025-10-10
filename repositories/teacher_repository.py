from sqlalchemy.orm import Session
from sqlalchemy import select, cast, String, func, update
from models.database import TeacherList
from typing import Optional, List

class TeacherRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_teacher(self, teacher_data: dict) -> TeacherList:
        teacher = TeacherList(**teacher_data)
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher
    
    def find_by_reg_user_id(self, reg_user_id: int) -> Optional[TeacherList]:
        query = select(TeacherList).where(TeacherList.regUserID == reg_user_id)
        return self.db.execute(query).scalar_one_or_none()
    
    def find_by_url_id(self, url_id: str) -> Optional[TeacherList]:
        query = select(TeacherList).where(
            cast(TeacherList.url_id, String) == url_id
        )
        return self.db.execute(query).scalar_one_or_none()
    
    def find_by_location_and_name(
        self, state: str, county: str, district: str, school: str, name: str
    ) -> Optional[TeacherList]:
        query = select(TeacherList).where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county) &
            (cast(TeacherList.district, String) == district) &
            (cast(TeacherList.school, String) == school) &
            (cast(TeacherList.name, String) == name)
        )
        return self.db.execute(query).scalar_one_or_none()
    
    def get_random_teacher(self) -> Optional[TeacherList]:
        query = select(TeacherList).order_by(func.newid()).limit(1)
        return self.db.execute(query).scalar_one_or_none()
    
    def update_teacher(self, reg_user_id: int, update_data: dict):
        query = update(TeacherList).where(
            TeacherList.regUserID == reg_user_id
        ).values(**update_data)
        self.db.execute(query)
        self.db.commit()
    
    def update_teacher_by_location(
        self, state: str, county: str, district: str, 
        school: str, name: str, update_data: dict
    ):
        query = update(TeacherList).where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county) &
            (cast(TeacherList.district, String) == district) &
            (cast(TeacherList.school, String) == school) &
            (cast(TeacherList.name, String) == name)
        ).values(**update_data)
        self.db.execute(query)
        self.db.commit()
    
    def get_teachers_by_location(
        self, state: str, county: str = None, 
        district: str = None, school: str = None
    ) -> List[TeacherList]:
        query = select(
            TeacherList.name, TeacherList.url_id
        ).where(cast(TeacherList.state, String) == state)
        
        if county:
            query = query.where(cast(TeacherList.county, String) == county)
        if district:
            query = query.where(cast(TeacherList.district, String) == district)
        if school:
            query = query.where(cast(TeacherList.school, String) == school)
        
        return self.db.execute(query).fetchall()
    
    def get_distinct_states(self) -> List[str]:
        states = self.db.query(
            cast(TeacherList.state, String)
        ).distinct().all()
        return sorted([state[0] for state in states])
    
    def get_distinct_counties(self, state: str) -> List[str]:
        query = select(
            cast(TeacherList.county, String)
        ).distinct().where(cast(TeacherList.state, String) == state)
        counties = self.db.execute(query).fetchall()
        return sorted([county[0] for county in counties])
    
    def get_distinct_districts(self, state: str, county: str) -> List[str]:
        query = select(
            cast(TeacherList.district, String)
        ).distinct().where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county)
        )
        districts = self.db.execute(query).fetchall()
        return sorted([district[0] for district in districts])
    
    def get_distinct_schools(
        self, state: str, county: str, district: str
    ) -> List[str]:
        query = select(
            cast(TeacherList.school, String)
        ).distinct().where(
            (cast(TeacherList.state, String) == state) &
            (cast(TeacherList.county, String) == county) &
            (cast(TeacherList.district, String) == district)
        )
        schools = self.db.execute(query).fetchall()
        return sorted([school[0] for school in schools])