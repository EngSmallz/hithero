from sqlalchemy.orm import Session
from sqlalchemy import select
from models.database import School
from typing import List

class SchoolRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_distinct_states(self) -> List[str]:
        states = self.db.query(School.state).distinct().all()
        return sorted([state[0] for state in states])
    
    def get_distinct_counties(self, state: str) -> List[str]:
        query = select(School.county).distinct().where(School.state == state)
        result = self.db.execute(query)
        counties = result.fetchall()
        return sorted([county[0] for county in counties])
    
    def get_distinct_districts(self, state: str, county: str) -> List[str]:
        query = select(School.district).distinct().where(
            (School.state == state) & (School.county == county)
        )
        result = self.db.execute(query)
        districts = result.fetchall()
        return sorted([district[0] for district in districts])
    
    def get_distinct_schools(
        self, state: str, county: str, district: str
    ) -> List[str]:
        query = select(School.school_name).distinct().where(
            (School.state == state) &
            (School.county == county) &
            (School.district == district)
        )
        result = self.db.execute(query)
        schools = result.fetchall()
        return sorted([school[0] for school in schools])
