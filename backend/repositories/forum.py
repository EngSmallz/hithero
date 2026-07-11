class ForumRepository:
    """Persistence operations for forum workflows."""

    def __init__(self, *, session_factory, post_model, comment_model=None, vote_model=None):
        self._session_factory = session_factory
        self._post_model = post_model
        self._comment_model = comment_model
        self._vote_model = vote_model

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

    def create_comment(self, *, post_id, user_id, content, parent_comment_id):
        db = self._session_factory()
        try:
            post = db.query(self._post_model).filter(
                self._post_model.id == post_id
            ).first()
            if not post:
                db.rollback()
                return None, "post"

            if parent_comment_id:
                parent_comment = (
                    db.query(self._comment_model)
                    .filter(self._comment_model.id == parent_comment_id)
                    .first()
                )
                if not parent_comment:
                    db.rollback()
                    return None, "parent"

            new_comment = self._comment_model(
                post_id=post_id,
                user_id=user_id,
                content=content,
                parent_comment_id=parent_comment_id,
            )
            db.add(new_comment)
            post.comment_count += 1
            db.commit()
            db.refresh(new_comment)
            return new_comment, None
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def record_vote(self, *, post_id, user_id, vote_type):
        db = self._session_factory()
        try:
            if vote_type not in (1, -1):
                raise ValueError(
                    "Invalid vote type. Must be 1 (upvote) or -1 (downvote)."
                )
            post = db.query(self._post_model).filter(
                self._post_model.id == post_id
            ).first()
            if not post:
                db.rollback()
                return None

            existing_vote = (
                db.query(self._vote_model)
                .filter(
                    self._vote_model.post_id == post_id,
                    self._vote_model.user_id == user_id,
                )
                .first()
            )
            if existing_vote:
                if existing_vote.vote_type == vote_type:
                    db.delete(existing_vote)
                    post.upvote_count -= vote_type
                else:
                    old_vote_value = existing_vote.vote_type
                    existing_vote.vote_type = vote_type
                    post.upvote_count += vote_type - old_vote_value
            else:
                db.add(
                    self._vote_model(
                        post_id=post_id,
                        user_id=user_id,
                        vote_type=vote_type,
                    )
                )
                post.upvote_count += vote_type

            db.commit()
            db.refresh(post)
            return post
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
