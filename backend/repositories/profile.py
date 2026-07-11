from sqlalchemy import String, cast, select, update


class ProfileRepository:
    """Persistence operations for teacher identity/profile lookups."""

    def __init__(self, *, session_factory, teacher_model):
        self._session_factory = session_factory
        self._teacher_model = teacher_model

    def _context_conditions(self, context):
        model_fields = {
            "state": "state",
            "county": "county",
            "district": "district",
            "school": "school",
            "teacher": "name",
        }
        return [
            cast(getattr(self._teacher_model, model_field), String)
            == context.get(context_field)
            for context_field, model_field in model_fields.items()
        ]

    def get_teacher_by_context(self, context):
        db = self._session_factory()
        try:
            result = db.execute(
                select(self._teacher_model).where(*self._context_conditions(context))
            ).fetchone()
            return result[0] if result else None
        finally:
            db.close()

    def get_teacher_by_user_id(self, user_id):
        db = self._session_factory()
        try:
            result = db.execute(
                select(self._teacher_model).where(
                    self._teacher_model.regUserID == user_id
                )
            ).fetchone()
            return result[0] if result else None
        finally:
            db.close()

    def update_teacher_school(self, user_id, *, state, county, district, school):
        self._update_teacher(
            user_id,
            state=state,
            county=county,
            district=district,
            school=school,
        )

    def update_teacher_name(self, user_id, name):
        self._update_teacher(user_id, name=name)

    def update_teacher_wishlist(self, user_id, wishlist_url):
        self._update_teacher(user_id, wishlist_url=wishlist_url)

    def _update_teacher(self, user_id, **values):
        db = self._session_factory()
        try:
            db.execute(
                update(self._teacher_model)
                .where(self._teacher_model.regUserID == user_id)
                .values(**values)
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
