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
