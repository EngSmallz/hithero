class ForumRepository:
    """Persistence operations for forum workflows."""

    def __init__(self, *, session_factory, post_model):
        self._session_factory = session_factory
        self._post_model = post_model

    def create_post(self, *, title, content, user_id):
        db = self._session_factory()
        try:
            post = self._post_model(
                title=title,
                content=content,
                user_id=user_id,
            )
            db.add(post)
            db.commit()
            db.refresh(post)
            return post
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
