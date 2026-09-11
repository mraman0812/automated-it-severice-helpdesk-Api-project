from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    ticket_id: int
    correct_category: str
    correct_subcategory: Optional[str] = None
    correct_priority: Optional[str] = None
    comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    correct_category: str
    correct_subcategory: Optional[str] = None
    correct_priority: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
