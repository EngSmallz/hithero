from sqlalchemy import String, cast, delete, select


class AdminRepository:
    """Persistence operations for administrator account workflows."""

    def __init__(
        self,
        *,
        session_factory,
        registered_user_model,
        teacher_model,
        pending_user_model=None,
    ):
        self._session_factory = session_factory
        self._registered_user_model = registered_user_model
        self._teacher_model = teacher_model
        self._pending_user_model = pending_user_model

    def delete_user_account(self, target_email):
        db = self._session_factory()
        try:
            user_id_result = db.execute(
                select(self._registered_user_model.id).where(
                    cast(self._registered_user_model.email, String)
                    == cast(target_email, String)
                )
            ).fetchone()
            if not user_id_result:
                return False

            target_user_id = user_id_result[0]
            db.execute(
                delete(self._teacher_model).where(
                    self._teacher_model.regUserID == target_user_id
                )
            )
            db.execute(
                delete(self._registered_user_model).where(
                    cast(self._registered_user_model.email, String)
                    == cast(target_email, String)
                )
            )
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def delete_pending_user(self, user_email):
        db = self._session_factory()
        try:
            user = db.execute(
                select(self._pending_user_model).where(
                    cast(self._pending_user_model.email, String)
                    == cast(user_email, String)
                )
            ).fetchone()
            if not user:
                db.rollback()
                return False
            db.execute(
                delete(self._pending_user_model).where(
                    cast(self._pending_user_model.email, String)
                    == cast(user_email, String)
                )
            )
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
