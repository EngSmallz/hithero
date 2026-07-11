from passlib.hash import sha256_crypt


class PasswordMismatch(ValueError):
    """Raised when reset password confirmation values differ."""


class InvalidResetToken(ValueError):
    """Raised when a reset token is absent, expired, or already used."""


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

    def create_reset_token(self, email, *, token, expires_at):
        if self._repository.get_registered_user_by_email(email) is None:
            return False
        self._repository.create_reset_token(
            email=email,
            token=token,
            expires_at=expires_at,
        )
        return True

    def reset_password(self, token, new_password, confirmed, *, now):
        if new_password != confirmed:
            raise PasswordMismatch("Passwords do not match.")

        reset = self._repository.get_valid_reset_token(token, now=now)
        if reset is None:
            raise InvalidResetToken("Invalid or expired reset token.")

        self._repository.consume_reset_token(
            token,
            reset.email,
            sha256_crypt.hash(new_password),
        )
