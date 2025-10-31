from sqlalchemy.orm import Session
from sqlalchemy import select, cast, String, insert, update, delete
from models.database import NewUsers, RegisteredUsers
from typing import Optional, List

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_registered_user_by_email(self, email: str) -> Optional[RegisteredUsers]:
        query = select(RegisteredUsers).where(
            cast(RegisteredUsers.email, String) == cast(email, String)
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def find_registered_user_by_id(self, id: int) -> Optional[RegisteredUsers]:
        query = select(RegisteredUsers).where(
            RegisteredUsers.id == id
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def find_new_user_by_email(self, email: str) -> Optional[NewUsers]:
        query = select(NewUsers).where(
            cast(NewUsers.email, String) == cast(email, String)
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def create_new_user(self, user_data: dict) -> NewUsers:
        new_user = NewUsers(**user_data)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
    
    def create_registered_user(self, user_data: dict) -> RegisteredUsers:
        query = insert(RegisteredUsers).values(**user_data)
        self.db.execute(query)
        self.db.commit()
    
    def delete_new_user(self, email: str):
        query = delete(NewUsers).where(
            cast(NewUsers.email, String) == cast(email, String)
        )
        self.db.execute(query)
        self.db.commit()
    
    def update_password(self, email: str, hashed_password: str):
        query = update(RegisteredUsers).where(
            cast(RegisteredUsers.email, String) == cast(email, String)
        ).values(password=hashed_password)
        self.db.execute(query)
        self.db.commit()
    
    def get_all_new_users(self) -> List[NewUsers]:
        query = select(NewUsers)
        result = self.db.execute(query)
        return result.scalars().all()
    
    def get_new_users_by_location(
        self, state: str, county: str, district: str
    ) -> List[NewUsers]:
        query = select(NewUsers).where(
            (cast(NewUsers.state, String) == state) &
            (cast(NewUsers.county, String) == county) &
            (cast(NewUsers.district, String) == district)
        )
        result = self.db.execute(query)
        return result.scalars().all()
    
    def update_user_create_count(self, user_id: int):
        query = update(RegisteredUsers).where(
            RegisteredUsers.id == user_id
        ).values(createCount=RegisteredUsers.createCount + 1)
        self.db.execute(query)
        self.db.commit()
    
    def get_users_without_profile(self) -> List[RegisteredUsers]:
        query = select(RegisteredUsers).where(RegisteredUsers.createCount == 0)
        return self.db.execute(query).scalars().all()
    
    def update_new_user_report(self, email: str):
        query = update(NewUsers).where(
            cast(NewUsers.email, String) == cast(email, String)
        ).values(report=1)
        self.db.execute(query)
        self.db.commit()
    
    def update_new_user_emailed(self, email: str):
        query = update(NewUsers).where(
            cast(NewUsers.email, String) == cast(email, String)
        ).values(emailed=1)
        self.db.execute(query)
        self.db.commit()