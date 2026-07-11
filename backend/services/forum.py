class ForumService:
    """Forum creation and workflow orchestration."""

    def __init__(self, repository):
        self._repository = repository

    def create_post(self, *, title, content, user_id, sanitize):
        return self._repository.create_post(
            title=sanitize(title),
            content=sanitize(content),
            user_id=user_id,
        )
