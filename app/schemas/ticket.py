from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.ticket import PriorityEnum, TicketStatusEnum


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    priority: Optional[PriorityEnum] = None
    status: Optional[TicketStatusEnum] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    department_id: Optional[int] = None
    assigned_to: Optional[int] = None
    resolution_note: Optional[str] = None


class TicketAssign(BaseModel):
    agent_id: int


class TicketResolve(BaseModel):
    resolution: str = Field(..., min_length=5, max_length=5000)


class TicketClassificationSummary(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[str] = None
    confidence: Optional[float] = 0.0


class TicketUserBrief(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TicketDepartmentBrief(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    status: str
    priority: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    subcategory_id: Optional[int] = None
    subcategory_name: Optional[str] = None
    created_by: int
    assigned_to: Optional[int] = None
    creator: Optional[TicketUserBrief] = None
    assignee: Optional[TicketUserBrief] = None
    department: Optional[TicketDepartmentBrief] = None
    
    # Classification details
    classification: Optional[TicketClassificationSummary] = None
    confidence_score: Optional[float] = 0.0
    needs_review: bool = False

    # SLA
    sla_deadline: Optional[datetime] = None
    sla_breached: bool = False

    # Resolution
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
