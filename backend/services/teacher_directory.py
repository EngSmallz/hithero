from typing import Optional

from backend.services.teachers import serialize_teacher_profile, serialize_teacher_summary


def _clean_optional_filter(value: Optional[str]):
    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


class TeacherDirectoryService:
    """Use cases for public teacher-directory reads."""

    def __init__(self, repository):
        self._repository = repository

    def build_directory_response(
        self,
        *,
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

        filters = {
            "state": state,
            "county": county,
            "district": district,
            "school": school,
        }
        total = self._repository.count_public_teachers(**filters)
        total_pages = (total + page_size - 1) // page_size if total else 0
        if total_pages:
            page = min(page, total_pages)
        offset = (page - 1) * page_size
        teachers = self._repository.list_public_teachers(
            **filters,
            offset=offset,
            limit=page_size,
        )

        return {
            "teachers": [serialize_teacher_summary(teacher) for teacher in teachers],
            "filters": self._repository.directory_filters(
                state=state,
                county=county,
                district=district,
            ),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "applied_filters": filters,
        }

    def get_public_teacher_profile(self, url_id: str):
        teacher = self._repository.get_public_teacher(url_id)
        if teacher is None:
            return None
        return serialize_teacher_profile(teacher)

    def get_school_states(self):
        return self._repository.get_school_states()

    def get_school_counties(self, state: str):
        values = self._repository.get_school_counties(state)
        return values or {"message": f"No counties found for state: {state}"}

    def get_school_districts(self, state: str, county: str):
        values = self._repository.get_school_districts(state, county)
        if values:
            return values
        return {"message": f"No districts found for state: {state} and county: {county}"}

    def get_school_names(self, state: str, county: str, district: str):
        values = self._repository.get_school_names(state, county, district)
        if values:
            return values
        return {
            "message": (
                f"No schools found for state: {state}, county: {county}, "
                f"and district: {district}"
            )
        }

    def get_index_states(self):
        return self._repository.get_index_states()

    def get_index_counties(self, state: str):
        values = self._repository.get_index_counties(state)
        return values or {"message": f"No counties found for state: {state}"}

    def get_index_districts(self, state: str, county: str):
        values = self._repository.get_index_districts(state, county)
        if values:
            return values
        return {"message": f"No districts found for state: {state} and county: {county}"}

    def get_index_schools(self, state: str, county: str, district: str):
        values = self._repository.get_index_schools(state, county, district)
        if values:
            return values
        return {
            "message": (
                f"No schools found for state: {state}, county: {county}, "
                f"and district: {district}"
            )
        }

    def find_index_teachers(self, *, state, county=None, district=None, school=None):
        teachers = self._repository.find_index_teachers(
            state=state,
            county=county,
            district=district,
            school=school,
        )
        if not teachers:
            return None
        return [{"name": teacher.name, "url_id": teacher.url_id} for teacher in teachers]
