"""Forum routes: posts, comments, voting, editing, and moderation."""
from typing import List, Optional
import bleach
from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import ALLOWED_ATTRS, ALLOWED_TAGS
from app.database import SessionLocal
from app.dependencies import get_current_id, get_current_role
from app.limiter import limiter
from app.models import ForumComment, ForumPost, PostVote
from app.schemas import PostUpdate, VoteInput
from app.utils import model_to_dict

router = APIRouter()

@router.post("/forum/create_post")
@limiter.limit("5/minute")
def create_post(request: Request, title: str = Form(...), content: str = Form(...), user_id: int = Depends(get_current_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="You must be logged in to post.")
    db: Session = SessionLocal()
    # 1. Create a new ForumPost instance
    new_post = ForumPost(
        title=bleach.clean(title, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True),
        content=bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True),
        user_id=user_id
    )
    try:
        # 2. Add to session and commit
        db.add(new_post)
        db.commit()
        # 3. Refresh to get the auto-generated ID and created_at timestamp
        db.refresh(new_post)
    except Exception as e:
        db.rollback()
        print(f"Database error during post creation: {e}")
        # Return a generic error to the user
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create post due to a server error."
        )
    # 4. Return the new post data
    return new_post

@router.get("/forum/get_posts")
def get_posts():
    """
    Retrieves a list of all forum posts.

    The resulting list is ordered by creation date (newest first).
    If you implement an upvote mechanism, you can modify the order_by clause
    to use upvotes first:
    .order_by(ForumPost.upvotes.desc(), ForumPost.created_at.desc())
    """
    db: Session = SessionLocal()
   
    try:
        # Query all posts and order them by the 'created_at' column descending.
        # This returns the newest posts first, which is a good default for a feed.
        posts = db.query(ForumPost).order_by(ForumPost.created_at.desc()).all()
        return posts
    except Exception as e:
        print(f"Database error during post retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve posts due to a server error."
        )

@router.get("/forum/get_post")
def get_post(post_id: int):
    """
    Retrieves a single forum post using its unique ID.
    
    Raises HTTPException 404 if the post is not found.
    """
    db: Session = SessionLocal()
    
    try:
        # Query the database for a single post matching the provided ID
        post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
        
        # Check if the post was found
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found."
            )
            
        return post
        
    except HTTPException:
        # Re-raise the 404 exception if it was already raised
        raise
    except Exception as e:
        print(f"Database error during single post retrieval (ID: {post_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve post due to a server error."
        )

@router.post("/forum/posts/{post_id}/vote")
def handle_post_vote(post_id: int, vote_data: VoteInput, user_id: int = Depends(get_current_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="You must be logged in to post.")

    db: Session = SessionLocal()
    vote_type = vote_data.vote_type

    # 1. Input validation
    if vote_type not in (1, -1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vote type. Must be 1 (upvote) or -1 (downvote)."
        )

    # 2. Check if the post exists
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with ID {post_id} not found.")

    # 3. Check for an existing vote by this user
    existing_vote = db.query(PostVote).filter(
        PostVote.post_id == post_id,
        PostVote.user_id == user_id
    ).first()

    try:
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Case 1: Retract vote (User clicks the same button again)
                db.delete(existing_vote)
                # Subtract the existing vote type from the post's count
                post.upvote_count -= vote_type
                
            else:
                # Case 2: Change vote (e.g., upvote to downvote or vice versa)
                old_vote_value = existing_vote.vote_type
                
                # Update the vote record with the new type
                existing_vote.vote_type = vote_type
                
                # Calculate net change and update the post's cached count
                # Net Change = (New Value) - (Old Value). This handles +/-2 changes.
                net_change = vote_type - old_vote_value
                post.upvote_count += net_change

        else:
            # Case 3: New vote
            new_vote = PostVote(post_id=post_id, user_id=user_id, vote_type=vote_type)
            db.add(new_vote)
            # Add the new vote type to the post's cached count
            post.upvote_count += vote_type

        # 4. Commit all changes to PostVote and ForumPost
        db.commit()
        db.refresh(post)

    except Exception as e:
        db.rollback()
        print(f"Database error during voting operation on post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A server error prevented the vote from being recorded."
        )

    # 5. Return the updated post data
    return post

@router.post("/forum/posts/{post_id}/comment", summary="Add a new comment to a specific post")
@limiter.limit("5/minute")
def add_comment_to_post(request: Request, post_id: int, content: str = Form(...), parent_comment_id: Optional[int] = Form(None), user_id: int = Depends(get_current_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="You must be logged in to post.")
    # Assuming SessionLocal() correctly creates a DB session
    db: Session = SessionLocal() 

    # 1. Check if the parent post exists
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Post with ID {post_id} not found."
        )

    # 2. Check if a parent comment exists (if parent_comment_id is provided, for nesting)
    if parent_comment_id:
        parent_comment = db.query(ForumComment).filter(ForumComment.id == parent_comment_id).first()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Parent comment with ID {parent_comment_id} not found."
            )

    try:
        # 3. Create a new ForumComment instance
        new_comment = ForumComment(
            post_id=post_id,
            user_id=user_id,
            content=bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True),
            parent_comment_id=parent_comment_id
        )
        # 4. Add to session
        db.add(new_comment)
        
        # 5. Update the comment_count on the parent post (Denormalization)
        post.comment_count += 1 
        
        db.commit()
        db.refresh(new_comment)

    except Exception as e:
        db.rollback()
        print(f"Database error during comment creation on post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create comment due to a server error."
        )

    # 6. Return the new comment data
    # Assuming the API returns the comment object, which includes 'user_id' and 'created_at'
    return new_comment

@router.get("/forum/comments/{post_id}/")
def get_comments_for_post(post_id: int = Path(..., gt=0),) -> List[dict]:
    """
    Fetches all comments associated with a specific post, ordered by creation date (newest first).
    """
    db: Session = SessionLocal()
    
    # 1. Check if the parent post exists (Optional, but good practice)
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Post with ID {post_id} not found."
        )

    try:
        # 2. Query all comments for that post ID
        comments = db.query(ForumComment)\
                     .filter(ForumComment.post_id == post_id)\
                     .order_by(desc(ForumComment.created_at))\
                     .all()

        # 3. FIX APPLIED HERE: Convert list of SQLAlchemy model objects to list of dictionaries
        return [model_to_dict(comment) for comment in comments] 

    except Exception as e:
        print(f"Database error during comment retrieval on post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve comments due to a server error."
        )

@router.delete("/forum/post/{post_id}/delete")
def delete_post(post_id: int, role: str = Depends(get_current_role)):
    """
    Deletes a post. Only allowed for role = 'admin'.
    """
    db: Session = SessionLocal()
    # 1. Authorization Check (Admin Only)
    if role != 'admin':
        print(f"User attempted unauthorized post deletion.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied: Only administrators can delete posts."
        )

    # 2. Find the post
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # 3. Delete the post
    db.delete(post)
    db.commit()
    
    # Due to CASCADE ON DELETE in the schema, votes and comments are automatically deleted.
    return

@router.delete("/forum/comment/{comment_id}/delete")
def delete_comment(comment_id: int, current_user_id: int = Depends(get_current_id),role: str = Depends(get_current_role)):
    """
    Deletes a comment. Only allowed for admin OR the comment's author (not yet but can be if you uncomment below)
    """
    db: Session = SessionLocal()
    # 1. Find the comment
    comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Comment not found"
        )
    
    # 2. Authorization Check (Admin OR Author)
    is_admin = (role == 'admin')
    #is_author = (comment.user_id == current_user_id)
    
    if not (is_admin): # or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied: You can only delete your own comments or be an administrator."
        )

    # 3. Denormalization: Decrement the parent post's comment count
    post = db.query(ForumPost).filter(ForumPost.id == comment.post_id).first()
    
    if post and post.comment_count > 0:
        post.comment_count -= 1
        # No need for db.add(post) if using SQLAlchemy and it's tracked by the session, 
        # but calling db.commit() below will save the change.
    
    # 4. Delete the comment
    db.delete(comment)
    db.commit()
    
    # Note on nested comments: If you need to handle deletion of child comments 
    # (i.e., comments that had replies) this would be handled automatically if 
    # you set up CASCADE DELETE on the parent_comment_id foreign key in your DDL.
    
    return {"detail": f"Comment ID {comment_id} successfully deleted."}

@router.patch("/forum/post/{post_id}/update")
async def update_post(post_id: int, post_data: PostUpdate, id: int = Depends(get_current_id)):
    """
    Allows the author of a post to update its title and content.
    """
    
    db: Session = SessionLocal()
    
    try:
        # 1. Fetch the existing post
        existing_post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
        
        if existing_post is None:
            raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found.")
            
        # 2. Authorization Check: Must be the original author
        # 'user' is the dictionary returned by get_current_active_user, containing the authenticated user's details
        if existing_post.user_id != id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to edit this post. You must be the author."
            )
            
        # 3. Update the post data in the SQLAlchemy model
        existing_post.title = bleach.clean(post_data.title, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
        existing_post.content = bleach.clean(post_data.content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
        
        # 4. Commit the changes to the database
        db.commit()
        
        # 5. Refresh the object to get any auto-updated fields (like a 'last_edited' timestamp if applicable)
        db.refresh(existing_post)
        
        # 6. Return the updated post
        # Note: We use response_model=PostUpdate for simplicity, 
        # but in a real app, you might use your full Post schema if it includes more fields.
        return existing_post
        
    except Exception as e:
        db.rollback() # Rollback the transaction on any error
        # In a production environment, log the error 'e' here
        raise HTTPException(status_code=500, detail="Internal server error during post update.")
        
    finally:
        db.close()

@router.patch("/forum/comment/{comment_id}/update")
async def update_comment(comment_id: int, content: str = Form(...), user: int = Depends(get_current_id)):
    """
    Allows the author of a comment to update its content.
    """
    db: Session = SessionLocal()
    
    try:
        # 1. Fetch the existing comment
        existing_comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
        
        if existing_comment is None:
            raise HTTPException(status_code=404, detail=f"Comment with ID {comment_id} not found.")
            
        # 2. Authorization Check: Must be the original author
        if existing_comment.user_id != user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to edit this comment. You must be the author."
            )
            
        # 3. Update the content
        existing_comment.content = bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
        
        
        # 4. Commit and Refresh
        db.commit()
        db.refresh(existing_comment)
        
        # Return the updated object (FastAPI handles JSON conversion)
        return existing_comment
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error during comment update.")
        
    finally:
        db.close()