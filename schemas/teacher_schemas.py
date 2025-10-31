from pydantic import BaseModel
from typing import Optional

class TeacherCreate(BaseModel):
    name: str
    state: str
    county: str
    district: str
    school: str
    aboutMe: str
    wishlist: str

class TeacherUpdate(BaseModel):
    aboutMe: Optional[str] = None
    name: Optional[str] = None
    wishlist: Optional[str] = None
    url_id: Optional[str] = None

class TeacherSchoolUpdate(BaseModel):
    state: str
    county: str
    district: str
    school: str

class TeacherResponse(BaseModel):
    name: str
    state: str
    county: str
    district: str
    school: str
    wishlist_url: str
    about_me: str
    image_data: Optional[str] = None