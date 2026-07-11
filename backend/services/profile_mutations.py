import re
import secrets


URL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
INVALID_URL_ID_MESSAGE = (
    "URL ID may only contain letters, numbers, hyphens, and underscores "
    "(3–50 characters)."
)


class InvalidTeacherUrlId(ValueError):
    """Raised when a teacher URL ID violates the legacy format contract."""


class TeacherUrlIdConflict(ValueError):
    """Raised when a teacher URL ID is already assigned to a profile."""


class ProfileMutationService:
    """Transactional profile mutation use cases."""

    def __init__(self, repository):
        self._repository = repository

    def update_teacher_school(self, user_id, *, state, county, district, school):
        self._repository.update_teacher_school(
            user_id,
            state=state,
            county=county,
            district=district,
            school=school,
        )

    def update_teacher_name(self, user_id, name):
        self._repository.update_teacher_name(user_id, name)

    def update_teacher_wishlist(self, user_id, wishlist):
        self._repository.update_teacher_wishlist(
            user_id,
            wishlist + "&tag=h0mer00mher0-20",
        )

    def update_teacher_url_id(self, user_id, url_id):
        if not URL_ID_PATTERN.match(url_id):
            raise InvalidTeacherUrlId(INVALID_URL_ID_MESSAGE)
        if self._repository.get_teacher_by_url_id(url_id) is not None:
            raise TeacherUrlIdConflict("URL ID already in use.")
        self._repository.update_teacher_url_id(user_id, url_id)

    def create_teacher_profile(
        self,
        user_id,
        role,
        email,
        *,
        name,
        state,
        county,
        district,
        school,
        about_me,
        wishlist,
    ):
        create_count = self._repository.get_profile_create_count(user_id)
        if create_count != 0 and role != "admin":
            return False

        first_part_email = email.split("@")[0]
        auto_url_id = f"{first_part_email}{secrets.randbelow(9999)}"
        while self._repository.get_teacher_by_url_id(auto_url_id) is not None:
            auto_url_id = f"{first_part_email}{secrets.randbelow(9999)}"

        self._repository.create_teacher_profile(
            user_id,
            name=name,
            state=state,
            county=county,
            district=district,
            school=school,
            about_me=about_me,
            wishlist_url=wishlist + "&tag=h0mer00mher0-20",
            url_id=auto_url_id,
        )
        return True
