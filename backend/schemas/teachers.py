from typing import List, Optional

from pydantic import BaseModel


class TeacherDirectorySummary(BaseModel):
    name: str
    url_id: str
    state: Optional[str] = None
    county: Optional[str] = None
    district: Optional[str] = None
    school: Optional[str] = None


class TeacherDirectoryFilters(BaseModel):
    states: List[str]
    counties: List[str]
    districts: List[str]
    schools: List[str]


class TeacherDirectoryResponse(BaseModel):
    teachers: List[TeacherDirectorySummary]
    filters: TeacherDirectoryFilters
    total: int
    page: int
    page_size: int
    total_pages: int
    applied_filters: dict[str, Optional[str]]


class TeacherProfileResponse(BaseModel):
    name: str
    url_id: str
    state: Optional[str] = None
    county: Optional[str] = None
    district: Optional[str] = None
    school: Optional[str] = None
    wishlist_url: Optional[str] = None
    about_me: Optional[str] = None
    image_data: Optional[str] = None


__all__ = [
    "TeacherDirectoryFilters",
    "TeacherDirectoryResponse",
    "TeacherDirectorySummary",
    "TeacherProfileResponse",
]
