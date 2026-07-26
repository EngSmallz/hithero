from backend.core.policies import require_forum_content_owner


class ForumService:
    """Forum creation and workflow orchestration."""

    def __init__(self, repository):
        self._repository = repository

    @staticmethod
    def serialize(record, *, model_to_dict, sanitize):
        data = model_to_dict(record)
        if "title" in data:
            data["title"] = sanitize(data["title"])
        if "content" in data:
            data["content"] = sanitize(data["content"])
        return data

    def get_posts(self):
        return self._repository.get_posts()

    def get_post(self, post_id):
        post = self._repository.get_post(post_id)
        if post is None:
            raise LookupError(f"Post with ID {post_id} not found.")
        return post

    def get_comments(self, post_id):
        comments = self._repository.get_comments(post_id)
        if comments is None:
            raise LookupError(f"Post with ID {post_id} not found.")
        return comments

    def create_post(self, *, title, content, user_id, sanitize):
        return self._repository.create_post(
            title=sanitize(title),
            content=sanitize(content),
            user_id=user_id,
        )

    def create_comment(
        self,
        *,
        post_id,
        user_id,
        content,
        parent_comment_id,
        sanitize,
    ):
        result, missing = self._repository.create_comment(
            post_id=post_id,
            user_id=user_id,
            content=sanitize(content),
            parent_comment_id=parent_comment_id,
        )
        if missing == "post":
            raise LookupError(f"Post with ID {post_id} not found.")
        if missing == "parent":
            raise LookupError(
                f"Parent comment with ID {parent_comment_id} not found."
            )
        return result

    def record_vote(self, *, post_id, user_id, vote_type):
        post = self._repository.record_vote(
            post_id=post_id,
            user_id=user_id,
            vote_type=vote_type,
        )
        if post is None:
            raise LookupError(f"Post with ID {post_id} not found.")
        return post

    def update_post(self, *, post_id, user_id, title, content, sanitize):
        post, error = self._repository.update_post(
            post_id=post_id,
            user_id=user_id,
            title=sanitize(title),
            content=sanitize(content),
        )
        if error == "missing":
            raise LookupError(f"Post with ID {post_id} not found.")
        if error == "forbidden":
            require_forum_content_owner(
                False,
                detail="Not authorized to edit this post. You must be the author.",
            )
        return post

    def update_comment(self, *, comment_id, user_id, content, sanitize):
        comment, error = self._repository.update_comment(
            comment_id=comment_id,
            user_id=user_id,
            content=sanitize(content),
        )
        if error == "missing":
            raise LookupError(f"Comment with ID {comment_id} not found.")
        if error == "forbidden":
            require_forum_content_owner(
                False,
                detail="Not authorized to edit this comment. You must be the author.",
            )
        return comment

    def delete_post(self, *, post_id, role):
        error = self._repository.delete_post(post_id=post_id, role=role)
        if error == "forbidden":
            raise PermissionError(
                "Access denied: Only administrators can delete posts."
            )
        if error == "missing":
            raise LookupError("Post not found")

    def delete_comment(self, *, comment_id, current_user_id, role):
        error = self._repository.delete_comment(
            comment_id=comment_id,
            current_user_id=current_user_id,
            role=role,
        )
        if error == "missing":
            raise LookupError("Comment not found")
        if error == "forbidden":
            require_forum_content_owner(
                False,
                detail=(
                    "Access denied: You can only delete your own comments or be an administrator."
                ),
            )
