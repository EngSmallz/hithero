class UserAccountNotFound(ValueError):
    """Raised when an administrator targets an unknown registered account."""


class PendingUserNotFound(ValueError):
    """Raised when an administrator targets an unknown pending user."""


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
