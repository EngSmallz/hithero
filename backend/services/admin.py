from backend.core.errors import ConflictError, ForbiddenError, NotFoundError
from backend.core.policies import require_teacher_district_scope


class UserAccountNotFound(NotFoundError):
    """Raised when an administrator targets an unknown registered account."""


class PendingUserNotFound(NotFoundError):
    """Raised when an administrator targets an unknown pending user."""


class ValidationScopeForbidden(ForbiddenError):
    """Raised when a teacher validates outside their district scope."""


class SchoolChangeRequestNotFound(NotFoundError):
    """Raised when a school-change request cannot be found."""


class SchoolChangeAlreadyReviewed(ConflictError):
    """Raised when a school-change request has already been decided."""


class SchoolChangeStale(ConflictError):
    """Raised when the teacher no longer matches the request's old values."""


class AdminService:
    """Administrator use cases that coordinate policy and persistence."""

    def __init__(self, repository):
        self._repository = repository

    def delete_user_account(self, target_email):
        if not self._repository.delete_user_account(target_email):
            raise UserAccountNotFound(target_email)
        return (
            "Successfully deleted account and associated data for target user: "
            f"{target_email}."
        )

    def delete_pending_user(self, user_email):
        if not self._repository.delete_pending_user(user_email):
            raise PendingUserNotFound(user_email)

    def validate_pending_user(self, user_email, *, role, current_user_id):
        email, error = self._repository.validate_pending_user(
            user_email,
            role=role,
            current_user_id=current_user_id,
        )
        if error == "missing":
            raise PendingUserNotFound(user_email)
        if error == "forbidden":
            require_teacher_district_scope(False, detail=user_email)
        return email

    def report_pending_user(self, user_email, *, role, current_user_id):
        return self._update_pending_flag(
            user_email,
            flag_name="report",
            role=role,
            current_user_id=current_user_id,
        )

    def mark_pending_user_emailed(self, user_email, *, role, current_user_id):
        return self._update_pending_flag(
            user_email,
            flag_name="emailed",
            role=role,
            current_user_id=current_user_id,
        )

    def get_validation_users(self, *, role, user_id):
        if role == "admin":
            return (
                None,
                self._repository.get_pending_users(),
                self._repository.get_school_change_requests(),
            )
        teacher = self._repository.get_teacher_by_user_id(user_id)
        if teacher is None:
            return None, [], []
        scope = {
            "state": teacher.state,
            "county": teacher.county,
            "district": teacher.district,
        }
        return (
            teacher,
            self._repository.get_pending_users(scope=scope),
            self._repository.get_school_change_requests(scope=scope),
        )

    def review_school_change(self, request_id, *, role, current_user_id, decision):
        change = self._repository.get_school_change_request(request_id)
        if change is None:
            raise SchoolChangeRequestNotFound(request_id)
        if change.status != "pending":
            raise SchoolChangeAlreadyReviewed(
                "This school-change request has already been reviewed."
            )

        if role == "teacher":
            teacher = self._repository.get_teacher_by_user_id(current_user_id)
            if (
                teacher is None
                or teacher.state != change.old_state
                or teacher.county != change.old_county
                or teacher.district != change.old_district
            ):
                raise ValidationScopeForbidden(
                    "You can only review school changes in your own district."
                )

        _, error = self._repository.decide_school_change(
            request_id,
            decision=decision,
            reviewed_by=current_user_id,
        )
        if error == "missing":
            raise SchoolChangeRequestNotFound(request_id)
        if error == "reviewed":
            raise SchoolChangeAlreadyReviewed(
                "This school-change request has already been reviewed."
            )
        if error == "stale":
            raise SchoolChangeStale(
                "The teacher profile no longer matches the requested old school values."
            )

    def build_teacher_report(self, *, state, county=None, district=None, school=None):
        rows = self._repository.get_teacher_report_rows(
            state=state,
            county=county,
            district=district,
            school=school,
        )
        if rows is None:
            return None
        data = ["Name\tSchool\tEmail\tPhone"]
        data.extend(
            f"{name}\t{school_name}\t{email}\t{phone}"
            for name, school_name, email, phone in rows
        )
        return "\n".join(data)

    def _update_pending_flag(self, user_email, *, flag_name, role, current_user_id):
        if not self._repository.update_pending_flag(
            user_email,
            flag_name=flag_name,
            flag_value=1,
            role=role,
            current_user_id=current_user_id,
        ):
            require_teacher_district_scope(False, detail=user_email)
