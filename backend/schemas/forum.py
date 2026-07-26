import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePostRequest(BaseModel):
    """Defines the expected input structure for creating a new forum post."""

    title: str
    content: str


class PostDisplay(BaseModel):
    """Schema for returning post data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    user_id: int
    created_at: datetime.datetime
    upvote_count: int
    comment_count: int


class VoteInput(BaseModel):
    """Defines the expected input structure for posting a vote."""

    vote_type: int = Field(..., description="1 for Upvote, -1 for Downvote")


class PostUpdate(BaseModel):
    """Schema for the data received when updating a post."""

    title: str
    content: str


__all__ = ["CreatePostRequest", "PostDisplay", "PostUpdate", "VoteInput"]
