from passlib.hash import sha256_crypt


class ProfileAuthService:
    """Registration and login use cases for the session-backed profile API."""

    def __init__(self, repository):
        self._repository = repository

    def register_user(
        self,
        *,
        name,
        email,
        phone_number,
        password,
        confirm_password,
        state,
        county,
        district,
        school,
    ):
        if self._repository.get_registered_user_by_email(email) is not None:
            return "User with this email already exists.", False
        if self._repository.get_pending_user_by_email(email) is not None:
            return (
                "User with this email is already in the registration queue.",
                False,
            )
        if password != confirm_password:
            return "Password do not match.", False

        self._repository.create_pending_user(
            name=name,
            email=email,
            state=state,
            county=county,
            district=district,
            school=school,
            phone_number=phone_number,
            password=sha256_crypt.hash(password),
        )
        return (
            "User registered successfully. You should recieve an email shortly. "
            "Please check your spam folder",
            True,
        )

    def authenticate_user(self, email, password):
        user = self._repository.get_registered_user_by_email(email)
        if user and sha256_crypt.verify(password, user.password):
            return user
        return None
