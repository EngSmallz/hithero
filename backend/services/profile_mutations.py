import re
import secrets
from urllib.parse import urlsplit, urlunsplit

from backend.core.errors import BadRequestError, ConflictError


URL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
INVALID_URL_ID_MESSAGE = (
    "URL ID may only contain letters, numbers, hyphens, and underscores "
    "(3–50 characters)."
)
INVALID_WISHLIST_URL_MESSAGE = "Please enter a valid shareable wishlist URL."


class InvalidTeacherUrlId(BadRequestError):
    """Raised when a teacher URL ID violates the legacy format contract."""


class TeacherUrlIdConflict(ConflictError):
    """Raised when a teacher URL ID is already assigned to a profile."""


class SchoolVerificationRequired(ConflictError):
    """Raised when approved school details are changed without re-verification."""


class SchoolChangeConfirmationRequired(BadRequestError):
    """Raised when a school-change request is submitted without confirmation."""


class InvalidSchoolChange(BadRequestError):
    """Raised when a proposed school is not in the approved school catalog."""


class SchoolChangeAlreadyPending(ConflictError):
    """Raised when a teacher already has a school-change request under review."""


class InvalidWishlistUrl(BadRequestError):
    """Raised when a wishlist URL cannot be normalized safely."""


def normalize_wishlist_url(wishlist):
    """Normalize a wishlist URL for storage without affiliate parameters."""
    value = (wishlist or "").strip()
    if not value:
        raise InvalidWishlistUrl(INVALID_WISHLIST_URL_MESSAGE)
    if not re.match(r"^https?://", value, re.IGNORECASE):
        value = f"https://{value.lstrip('/')}"

    parsed = urlsplit(value)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.netloc
        or not parsed.hostname
        or any(character.isspace() for character in value)
    ):
        raise InvalidWishlistUrl(INVALID_WISHLIST_URL_MESSAGE)

    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc,
            parsed.path,
            "",
            parsed.fragment,
        )
    )


class TeacherImageTooLarge(BadRequestError):
    """Raised when an uploaded teacher image exceeds the configured limit."""


class InvalidTeacherImage(BadRequestError):
    """Raised when an uploaded teacher image has an unsupported MIME type."""


IMAGE_TOO_LARGE_MESSAGE = "File size exceeds the allowed limit"
INVALID_IMAGE_MESSAGE = (
    "Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."
)


class ProfileMutationService:
    """Transactional profile mutation use cases."""

    def __init__(self, repository):
        self._repository = repository

    def _get_verified_registration(self, user_id, *, db=None):
        getter = getattr(self._repository, "get_verified_registration", None)
        if getter is None:
            return None
        try:
            return getter(user_id, db=db)
        except TypeError:
            return getter(user_id)

    def _enforce_verified_school(
        self, user_id, *, state, county, district, school, db=None
    ):
        registration = self._get_verified_registration(user_id, db=db)
        if not registration:
            return
        expected = {
            "state": registration["registration_state"],
            "county": registration["registration_county"],
            "district": registration["registration_district"],
            "school": registration["registration_school"],
        }
        submitted = {
            "state": state,
            "county": county,
            "district": district,
            "school": school,
        }
        if submitted != expected:
            raise SchoolVerificationRequired(
                "School information was verified during registration. "
                "Contact support to request a school change."
            )

    def update_teacher_school(self, user_id, *, state, county, district, school):
        self._enforce_verified_school(
            user_id,
            state=state,
            county=county,
            district=district,
            school=school,
        )
        self._repository.update_teacher_school(
            user_id,
            state=state,
            county=county,
            district=district,
            school=school,
        )

    def request_teacher_school_change(
        self,
        user_id,
        *,
        state,
        county,
        district,
        school,
        confirmed,
    ):
        if not confirmed:
            raise SchoolChangeConfirmationRequired(
                "Confirm that you understand your profile will be removed from "
                "public and search results until the new school is reapproved."
            )

        proposed = {
            "state": state,
            "county": county,
            "district": district,
            "school": school,
        }
        with self._repository.transaction() as db:
            teacher = self._repository.get_teacher_by_user_id(user_id, db=db)
            registration = self._get_verified_registration(user_id, db=db)
            if teacher is None or registration is None:
                raise SchoolVerificationRequired(
                    "A verified school record is required before requesting a school change."
                )

            old = {
                "state": teacher.state,
                "county": teacher.county,
                "district": teacher.district,
                "school": teacher.school,
            }
            verified = {
                "state": registration["registration_state"],
                "county": registration["registration_county"],
                "district": registration["registration_district"],
                "school": registration["registration_school"],
            }
            if old != verified:
                raise SchoolVerificationRequired(
                    "The current profile does not match its verified school record. "
                    "Contact support before requesting another school change."
                )
            if old == proposed:
                raise InvalidSchoolChange("Choose a different school for the requested change.")
            if not self._repository.school_exists(**proposed, db=db):
                raise InvalidSchoolChange(
                    "The proposed school could not be verified in the school directory."
                )
            if (
                teacher.school_change_pending
                or self._repository.get_pending_school_change(user_id, db=db) is not None
            ):
                raise SchoolChangeAlreadyPending(
                    "A school change is already awaiting review."
                )

            self._repository.create_school_change_request(
                user_id,
                old_state=old["state"],
                old_county=old["county"],
                old_district=old["district"],
                old_school=old["school"],
                proposed_state=state,
                proposed_county=county,
                proposed_district=district,
                proposed_school=school,
                db=db,
            )

    def update_teacher_name(self, user_id, name):
        self._repository.update_teacher_name(user_id, name)

    def update_teacher_wishlist(self, user_id, wishlist):
        self._repository.update_teacher_wishlist(
            user_id,
            normalize_wishlist_url(wishlist),
        )

    def update_teacher_about_me(self, user_id, about_me):
        self._repository.update_teacher_about_me(user_id, about_me)

    def update_teacher_url_id(self, user_id, url_id):
        if not URL_ID_PATTERN.match(url_id):
            raise InvalidTeacherUrlId(INVALID_URL_ID_MESSAGE)
        if self._repository.get_teacher_by_url_id(url_id) is not None:
            raise TeacherUrlIdConflict("URL ID already in use.")
        self._repository.update_teacher_url_id(user_id, url_id)

    def update_teacher_image(
        self,
        user_id,
        role,
        image_bytes,
        *,
        image_size,
        max_file_size,
        detect_file_type,
    ):
        if image_size > max_file_size:
            raise TeacherImageTooLarge(IMAGE_TOO_LARGE_MESSAGE)

        allowed_mime_types = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
        }
        results = detect_file_type(image_bytes)
        detected_type = None
        if results:
            detected_type = getattr(results[0], "mime", None)
            if detected_type is None:
                detected_type = getattr(results[0], "mime_type", None)
        if detected_type not in allowed_mime_types:
            raise InvalidTeacherImage(INVALID_IMAGE_MESSAGE)

        if role:
            self._repository.update_teacher_image(user_id, image_bytes)
            return True
        return False

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
        with self._repository.transaction() as db:
            create_count = self._repository.get_profile_create_count(
                user_id,
                db=db,
            )
            if create_count != 0 and role != "admin":
                return False

            self._enforce_verified_school(
                user_id,
                state=state,
                county=county,
                district=district,
                school=school,
                db=db,
            )

            first_part_email = email.split("@")[0]
            auto_url_id = f"{first_part_email}{secrets.randbelow(9999)}"
            while (
                self._repository.get_teacher_by_url_id(auto_url_id, db=db)
                is not None
            ):
                auto_url_id = f"{first_part_email}{secrets.randbelow(9999)}"

            self._repository.create_teacher_profile(
                user_id,
                name=name,
                state=state,
                county=county,
                district=district,
                school=school,
                about_me=about_me,
                wishlist_url=normalize_wishlist_url(wishlist),
                url_id=auto_url_id,
                db=db,
            )
        return True
