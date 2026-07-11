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
