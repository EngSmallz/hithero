import html
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, Response, status

from backend.repositories.forum import ForumRepository
from backend.core.errors import ForbiddenError
from backend.core.policies import require_admin, require_authenticated_user
from backend.services.forum import ForumService


logger = logging.getLogger(__name__)


def create_forum_router(
    *,
    session_factory,
    post_model,
    comment_model,
    vote_model,
    vote_input_model,
    post_update_model,
    get_current_id,
    get_current_role,
    limiter,
    clean_html,
    allowed_tags,
    allowed_attrs,
    allowed_protocols,
    model_to_dict,
):
    router = APIRouter(prefix="/forum")
    forum_repository = ForumRepository(
        session_factory=session_factory,
        post_model=post_model,
        comment_model=comment_model,
        vote_model=vote_model,
    )
    forum_service = ForumService(forum_repository)

    def sanitize(value: str):
        decoded = value or ""
        for _ in range(10):
            unescaped = html.unescape(decoded)
            if unescaped == decoded:
                break
            decoded = unescaped

        return clean_html(
            decoded,
            tags=allowed_tags,
            attributes=allowed_attrs,
            protocols=allowed_protocols,
            strip=True,
        ).strip()

    def serialize(record):
        data = model_to_dict(record)
        if "title" in data:
            data["title"] = sanitize(data["title"])
        if "content" in data:
            data["content"] = sanitize(data["content"])
        return data

    @router.post("/create_post")
    @limiter.limit("5/minute")
    def create_post(
        request: Request,
        title: str = Form(...),
        content: str = Form(...),
        user_id: int = Depends(get_current_id),
    ):
        user_id = require_authenticated_user(
            user_id,
            detail="You must be logged in to post.",
        )

        try:
            new_post = forum_service.create_post(
                title=title,
                content=content,
                user_id=user_id,
                sanitize=sanitize,
            )
        except Exception as exc:
            logger.exception("Database error during post creation")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create post due to a server error.",
            )
        return serialize(new_post)

    @router.get("/get_posts")
    def get_posts():
        try:
            return [
                forum_service.serialize(
                    post,
                    model_to_dict=model_to_dict,
                    sanitize=sanitize,
                )
                for post in forum_service.get_posts()
            ]
        except Exception as exc:
            logger.exception("Database error during post retrieval")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve posts due to a server error.",
            )

    @router.get("/get_post")
    def get_post(post_id: int):
        try:
            post = forum_service.get_post(post_id)
            return forum_service.serialize(
                post,
                model_to_dict=model_to_dict,
                sanitize=sanitize,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            logger.exception("Database error during single post retrieval", extra={"post_id": post_id})
            raise HTTPException(
                status_code=500,
                detail="Could not retrieve post due to a server error.",
            )

    @router.post("/posts/{post_id}/vote")
    def handle_post_vote(
        post_id: int,
        vote_data: vote_input_model,
        user_id: int = Depends(get_current_id),
    ):
        user_id = require_authenticated_user(
            user_id,
            detail="You must be logged in to post.",
        )

        try:
            post = forum_service.record_vote(
                post_id=post_id,
                user_id=user_id,
                vote_type=vote_data.vote_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.exception("Database error during voting operation", extra={"post_id": post_id})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A server error prevented the vote from being recorded.",
            )
        return serialize(post)

    @router.post(
        "/posts/{post_id}/comment",
        summary="Add a new comment to a specific post",
    )
    @limiter.limit("5/minute")
    def add_comment_to_post(
        request: Request,
        post_id: int,
        content: str = Form(...),
        parent_comment_id: Optional[int] = Form(None),
        user_id: int = Depends(get_current_id),
    ):
        user_id = require_authenticated_user(
            user_id,
            detail="You must be logged in to post.",
        )

        try:
            new_comment = forum_service.create_comment(
                post_id=post_id,
                user_id=user_id,
                content=content,
                parent_comment_id=parent_comment_id,
                sanitize=sanitize,
            )
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.exception("Database error during comment creation", extra={"post_id": post_id})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create comment due to a server error.",
            )
        return serialize(new_comment)

    @router.get("/comments/{post_id}/")
    def get_comments_for_post(post_id: int = Path(..., gt=0)) -> List[dict]:
        try:
            comments = forum_service.get_comments(post_id)
            return [
                forum_service.serialize(
                    comment,
                    model_to_dict=model_to_dict,
                    sanitize=sanitize,
                )
                for comment in comments
            ]
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            logger.exception("Database error during comment retrieval", extra={"post_id": post_id})
            raise HTTPException(
                status_code=500,
                detail="Could not retrieve comments due to a server error.",
            )

    @router.delete("/post/{post_id}/delete")
    def delete_post(
        post_id: int,
        role: str = Depends(get_current_role),
    ):
        require_admin(
            role,
            detail="Access denied: Only administrators can delete posts.",
        )
        try:
            forum_service.delete_post(post_id=post_id, role=role)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (PermissionError, ForbiddenError) as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except Exception as exc:
            logger.exception("Database error during post deletion", extra={"post_id": post_id})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete post due to a server error.",
            )

    @router.delete("/comment/{comment_id}/delete")
    def delete_comment(
        comment_id: int,
        current_user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        current_user_id = require_authenticated_user(current_user_id)
        try:
            forum_service.delete_comment(
                comment_id=comment_id,
                current_user_id=current_user_id,
                role=role,
            )
            return {"detail": f"Comment ID {comment_id} successfully deleted."}
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (PermissionError, ForbiddenError) as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except Exception as exc:
            logger.exception(
                "Database error during comment deletion",
                extra={"comment_id": comment_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete comment due to a server error.",
            )

    @router.patch("/post/{post_id}/update")
    async def update_post(
        post_id: int,
        post_data: post_update_model,
        user_id: int = Depends(get_current_id),
    ):
        user_id = require_authenticated_user(user_id)
        try:
            post = forum_service.update_post(
                post_id=post_id,
                user_id=user_id,
                title=post_data.title,
                content=post_data.content,
                sanitize=sanitize,
            )
            return serialize(post)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (PermissionError, ForbiddenError) as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except Exception:
            logger.exception("Internal server error during post update", extra={"post_id": post_id})
            raise HTTPException(
                status_code=500,
                detail="Internal server error during post update.",
            )

    @router.patch("/comment/{comment_id}/update")
    async def update_comment(
        comment_id: int,
        content: str = Form(...),
        user_id: int = Depends(get_current_id),
    ):
        user_id = require_authenticated_user(user_id)
        try:
            comment = forum_service.update_comment(
                comment_id=comment_id,
                user_id=user_id,
                content=content,
                sanitize=sanitize,
            )
            return serialize(comment)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (PermissionError, ForbiddenError) as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except Exception:
            logger.exception(
                "Internal server error during comment update",
                extra={"comment_id": comment_id},
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error during comment update.",
            )

    return router
