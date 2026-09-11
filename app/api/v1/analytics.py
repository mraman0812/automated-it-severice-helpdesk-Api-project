from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.schemas.analytics import (
    TicketStats,
    CategoryDistribution,
    PriorityDistribution,
    SLAAnalytics,
    AgentWorkload,
    MLAccuracyStats,
)
from app.api.deps import require_roles
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/tickets", response_model=TicketStats)
def get_ticket_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.AGENT, RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    return AnalyticsService.get_ticket_stats(db)


@router.get("/categories", response_model=CategoryDistribution)
def get_category_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.AGENT, RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    return AnalyticsService.get_category_distribution(db)


@router.get("/priorities", response_model=PriorityDistribution)
def get_priority_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.AGENT, RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    return AnalyticsService.get_priority_distribution(db)


@router.get("/sla", response_model=SLAAnalytics)
def get_sla_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    return AnalyticsService.get_sla_analytics(db)


@router.get("/agents", response_model=List[AgentWorkload])
def get_agent_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    return AnalyticsService.get_agent_workloads(db)


@router.get("/ml", response_model=MLAccuracyStats)
def get_ml_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    return AnalyticsService.get_ml_accuracy_stats(db)
