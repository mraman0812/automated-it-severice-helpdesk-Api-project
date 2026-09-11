from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CommentUser(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = False


class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    user: CommentUser
    comment: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
