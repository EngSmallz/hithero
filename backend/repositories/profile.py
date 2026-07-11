from sqlalchemy import String, cast, insert, select, update


class ProfileRepository:
    """Persistence operations for teacher identity/profile lookups."""

    def __init__(self, *, session_factory, teacher_model, registered_user_model=None):
        self._session_factory = session_factory
        self._teacher_model = teacher_model
        self._registered_user_model = registered_user_model

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

    def get_teacher_by_url_id(self, url_id):
        db = self._session_factory()
        try:
            result = db.execute(
                select(self._teacher_model).where(
                    cast(self._teacher_model.url_id, String) == cast(url_id, String)
                )
            ).fetchone()
            return result[0] if result else None
        finally:
            db.close()

    def update_teacher_url_id(self, user_id, url_id):
        self._update_teacher(user_id, url_id=url_id)

    def update_teacher_image(self, user_id, image_bytes):
        self._update_teacher(user_id, image_data=image_bytes)

    def get_profile_create_count(self, user_id):
        db = self._session_factory()
        try:
            return db.execute(
                select(self._registered_user_model.createCount).where(
                    self._registered_user_model.id == user_id
                )
            ).scalar()
        finally:
            db.close()

    def create_teacher_profile(self, user_id, *, name, state, county, district,
                               school, about_me, wishlist_url, url_id):
        db = self._session_factory()
        try:
            db.execute(
                insert(self._teacher_model).values(
                    name=name,
                    state=state,
                    county=county,
                    district=district,
                    school=school,
                    regUserID=user_id,
                    about_me=about_me,
                    wishlist_url=wishlist_url,
                    url_id=url_id,
                )
            )
            db.execute(
                update(self._registered_user_model)
                .where(self._registered_user_model.id == user_id)
                .values(createCount=self._registered_user_model.createCount + 1)
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

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
