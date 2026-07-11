import html
from contextlib import contextmanager
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, Response, status
from sqlalchemy import desc

from backend.repositories.forum import ForumRepository
from backend.services.forum import ForumService


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

    @contextmanager
    def forum_session():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    def rollback_session(db):
        try:
            db.rollback()
        except Exception as exc:
            print(f"Database error during rollback: {exc}")

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
        if not user_id:
            raise HTTPException(status_code=401, detail="You must be logged in to post.")

        try:
            new_post = forum_service.create_post(
                title=title,
                content=content,
                user_id=user_id,
                sanitize=sanitize,
            )
        except Exception as exc:
            print(f"Database error during post creation: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create post due to a server error.",
            )
        return serialize(new_post)

    @router.get("/get_posts")
    def get_posts():
        with forum_session() as db:
            try:
                posts = db.query(post_model).order_by(post_model.created_at.desc()).all()
                return [serialize(post) for post in posts]
            except Exception as exc:
                print(f"Database error during post retrieval: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not retrieve posts due to a server error.",
                )

    @router.get("/get_post")
    def get_post(post_id: int):
        with forum_session() as db:
            try:
                post = db.query(post_model).filter(post_model.id == post_id).first()
                if post is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Post with ID {post_id} not found.",
                    )
                return serialize(post)
            except HTTPException:
                raise
            except Exception as exc:
                print(f"Database error during single post retrieval (ID: {post_id}): {exc}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not retrieve post due to a server error.",
                )

    @router.post("/posts/{post_id}/vote")
    def handle_post_vote(
        post_id: int,
        vote_data: vote_input_model,
        user_id: int = Depends(get_current_id),
    ):
        if not user_id:
            raise HTTPException(status_code=401, detail="You must be logged in to post.")

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
            print(f"Database error during voting operation on post {post_id}: {exc}")
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
        if not user_id:
            raise HTTPException(status_code=401, detail="You must be logged in to post.")

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
            print(f"Database error during comment creation on post {post_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create comment due to a server error.",
            )
        return serialize(new_comment)

    @router.get("/comments/{post_id}/")
    def get_comments_for_post(post_id: int = Path(..., gt=0)) -> List[dict]:
        with forum_session() as db:
            try:
                post = db.query(post_model).filter(post_model.id == post_id).first()
                if not post:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Post with ID {post_id} not found.",
                    )

                comments = (
                    db.query(comment_model)
                    .filter(comment_model.post_id == post_id)
                    .order_by(desc(comment_model.created_at))
                    .all()
                )
                return [serialize(comment) for comment in comments]
            except HTTPException:
                raise
            except Exception as exc:
                print(f"Database error during comment retrieval on post {post_id}: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not retrieve comments due to a server error.",
                )

    @router.delete("/post/{post_id}/delete")
    def delete_post(
        post_id: int,
        role: str = Depends(get_current_role),
    ):
        with forum_session() as db:
            try:
                if role != "admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Only administrators can delete posts.",
                    )

                post = db.query(post_model).filter(post_model.id == post_id).first()
                if not post:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post not found",
                    )

                db.delete(post)
                db.commit()
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            except HTTPException:
                rollback_session(db)
                raise
            except Exception as exc:
                rollback_session(db)
                print(f"Database error during post deletion (ID: {post_id}): {exc}")
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
        with forum_session() as db:
            try:
                comment = (
                    db.query(comment_model)
                    .filter(comment_model.id == comment_id)
                    .first()
                )
                if not comment:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Comment not found",
                    )

                is_admin = role == "admin"
                is_author = comment.user_id == current_user_id
                if not (is_admin or is_author):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Access denied: You can only delete your own comments "
                            "or be an administrator."
                        ),
                    )

                post = (
                    db.query(post_model)
                    .filter(post_model.id == comment.post_id)
                    .first()
                )
                if post and post.comment_count > 0:
                    post.comment_count -= 1

                db.delete(comment)
                db.commit()
                return {"detail": f"Comment ID {comment_id} successfully deleted."}
            except HTTPException:
                rollback_session(db)
                raise
            except Exception as exc:
                rollback_session(db)
                print(f"Database error during comment deletion (ID: {comment_id}): {exc}")
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
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except Exception:
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
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Internal server error during comment update.",
            )

    return router
