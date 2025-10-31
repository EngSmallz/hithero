from sqlalchemy.orm import Session
from sqlalchemy import select, cast, String, delete
from models.database import Spotlight
from typing import Optional

class SpotlightRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_token(self, token: str) -> Optional[Spotlight]:
        query = select(Spotlight).where(
            cast(Spotlight.token, String) == cast(token, String)
        )
        return self.db.execute(query).scalar_one_or_none()
    
    def delete_by_token(self, token: str):
        query = delete(Spotlight).where(
            cast(Spotlight.token, String) == cast(token, String)
        )
        self.db.execute(query)
        self.db.commit()
    
    def create_spotlight(self, spotlight_data: dict) -> Spotlight:
        spotlight = Spotlight(**spotlight_data)
        self.db.add(spotlight)
        self.db.commit()
        self.db.refresh(spotlight)
        return spotlight
    
    def upsert_spotlight(self, spotlight_data: dict, token: str):
        """Delete existing spotlight with token and create new one"""
        self.delete_by_token(token)
        return self.create_spotlight(spotlight_data)