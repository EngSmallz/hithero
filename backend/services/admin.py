class UserAccountNotFound(ValueError):
    """Raised when an administrator targets an unknown registered account."""


class PendingUserNotFound(ValueError):
    """Raised when an administrator targets an unknown pending user."""


class ValidationScopeForbidden(ValueError):
    """Raised when a teacher validates outside their district scope."""


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
            raise ValidationScopeForbidden(user_email)
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

    def _update_pending_flag(self, user_email, *, flag_name, role, current_user_id):
        if not self._repository.update_pending_flag(
            user_email,
            flag_name=flag_name,
            flag_value=1,
            role=role,
            current_user_id=current_user_id,
        ):
            raise ValidationScopeForbidden(user_email)
