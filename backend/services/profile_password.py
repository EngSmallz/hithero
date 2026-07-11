from passlib.hash import sha256_crypt


class ProfilePasswordService:
    """Password update use cases for authenticated profile users."""

    def __init__(self, repository):
        self._repository = repository

    def update_password(self, user_id, old_password, new_password, confirmed):
        if new_password != confirmed:
            return {"message": "New passwords do not match."}

        old_password_hash = self._repository.get_password_hash(user_id)
        if (
            not old_password_hash
            or not sha256_crypt.verify(old_password, old_password_hash)
        ):
            return {"message": "Invalid old password"}

        self._repository.update_password(
            user_id,
            sha256_crypt.hash(new_password),
        )
        return {
            "status": "success",
            "message": "Password updated successfully",
        }
