from typing import Dict, List, Optional
from pydantic import BaseModel


class TicketStats(BaseModel):
    total: int
    open: int
    classified: int
    assigned: int
    in_progress: int
    waiting_for_user: int
    resolved: int
    closed: int
    reopened: int
    needs_review: int


class CategoryDistribution(BaseModel):
    distribution: Dict[str, int]


class PriorityDistribution(BaseModel):
    distribution: Dict[str, int]


class StatusDistribution(BaseModel):
    distribution: Dict[str, int]


class SLAAnalytics(BaseModel):
    average_resolution_time_hours: float
    sla_breaches: int
    sla_compliance: float
    total_tracked: int


class AgentWorkload(BaseModel):
    agent_id: int
    agent_name: str
    department_name: Optional[str] = None
    active_tickets: int
    resolved_tickets: int


class MLAccuracyStats(BaseModel):
    total_predictions: int
    feedback_collected: int
    correct_predictions: int
    accuracy_percentage: float
    needs_review_count: int
