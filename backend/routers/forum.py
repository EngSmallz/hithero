from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, Response, status
from sqlalchemy import desc


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
    model_to_dict,
):
    router = APIRouter(prefix="/forum")

    def sanitize(value: str):
        return clean_html(
            value,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True,
        )

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

        db = session_factory()
        new_post = post_model(
            title=sanitize(title),
            content=sanitize(content),
            user_id=user_id,
        )
        try:
            db.add(new_post)
            db.commit()
            db.refresh(new_post)
        except Exception as exc:
            db.rollback()
            print(f"Database error during post creation: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create post due to a server error.",
            )
        return new_post

    @router.get("/get_posts")
    def get_posts():
        db = session_factory()
        try:
            return db.query(post_model).order_by(post_model.created_at.desc()).all()
        except Exception as exc:
            print(f"Database error during post retrieval: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve posts due to a server error.",
            )

    @router.get("/get_post")
    def get_post(post_id: int):
        db = session_factory()
        try:
            post = db.query(post_model).filter(post_model.id == post_id).first()
            if post is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Post with ID {post_id} not found.",
                )
            return post
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

        db = session_factory()
        vote_type = vote_data.vote_type
        if vote_type not in (1, -1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vote type. Must be 1 (upvote) or -1 (downvote).",
            )

        post = db.query(post_model).filter(post_model.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found.",
            )

        existing_vote = (
            db.query(vote_model)
            .filter(
                vote_model.post_id == post_id,
                vote_model.user_id == user_id,
            )
            .first()
        )

        try:
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
                    vote_model(
                        post_id=post_id,
                        user_id=user_id,
                        vote_type=vote_type,
                    )
                )
                post.upvote_count += vote_type

            db.commit()
            db.refresh(post)
        except Exception as exc:
            db.rollback()
            print(f"Database error during voting operation on post {post_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A server error prevented the vote from being recorded.",
            )
        return post

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

        db = session_factory()
        post = db.query(post_model).filter(post_model.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found.",
            )

        if parent_comment_id:
            parent_comment = (
                db.query(comment_model)
                .filter(comment_model.id == parent_comment_id)
                .first()
            )
            if not parent_comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent comment with ID {parent_comment_id} not found.",
                )

        try:
            new_comment = comment_model(
                post_id=post_id,
                user_id=user_id,
                content=sanitize(content),
                parent_comment_id=parent_comment_id,
            )
            db.add(new_comment)
            post.comment_count += 1
            db.commit()
            db.refresh(new_comment)
        except Exception as exc:
            db.rollback()
            print(f"Database error during comment creation on post {post_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create comment due to a server error.",
            )
        return new_comment

    @router.get("/comments/{post_id}/")
    def get_comments_for_post(post_id: int = Path(..., gt=0)) -> List[dict]:
        db = session_factory()
        post = db.query(post_model).filter(post_model.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found.",
            )

        try:
            comments = (
                db.query(comment_model)
                .filter(comment_model.post_id == post_id)
                .order_by(desc(comment_model.created_at))
                .all()
            )
            return [model_to_dict(comment) for comment in comments]
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
        db = session_factory()
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
        finally:
            db.close()

    @router.delete("/comment/{comment_id}/delete")
    def delete_comment(
        comment_id: int,
        current_user_id: int = Depends(get_current_id),
        role: str = Depends(get_current_role),
    ):
        db = session_factory()
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
        finally:
            db.close()

    @router.patch("/post/{post_id}/update")
    async def update_post(
        post_id: int,
        post_data: post_update_model,
        user_id: int = Depends(get_current_id),
    ):
        db = session_factory()
        try:
            existing_post = (
                db.query(post_model).filter(post_model.id == post_id).first()
            )
            if existing_post is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Post with ID {post_id} not found.",
                )
            if existing_post.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to edit this post. You must be the author.",
                )

            existing_post.title = sanitize(post_data.title)
            existing_post.content = sanitize(post_data.content)
            db.commit()
            db.refresh(existing_post)
            return existing_post
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Internal server error during post update.",
            )
        finally:
            db.close()

    @router.patch("/comment/{comment_id}/update")
    async def update_comment(
        comment_id: int,
        content: str = Form(...),
        user_id: int = Depends(get_current_id),
    ):
        db = session_factory()
        try:
            existing_comment = (
                db.query(comment_model)
                .filter(comment_model.id == comment_id)
                .first()
            )
            if existing_comment is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Comment with ID {comment_id} not found.",
                )
            if existing_comment.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Not authorized to edit this comment. "
                        "You must be the author."
                    ),
                )

            existing_comment.content = sanitize(content)
            db.commit()
            db.refresh(existing_comment)
            return existing_comment
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Internal server error during comment update.",
            )
        finally:
            db.close()

    return router
