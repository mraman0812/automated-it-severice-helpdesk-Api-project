from typing import Dict, Any, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatusEnum, PriorityEnum
from app.models.category import Category
from app.models.department import Department
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.models.classification import TicketClassification, ClassificationFeedback
from app.schemas.analytics import (
    TicketStats,
    CategoryDistribution,
    PriorityDistribution,
    StatusDistribution,
    SLAAnalytics,
    AgentWorkload,
    MLAccuracyStats,
)
from datetime import datetime, timezone
from typing import Optional


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AnalyticsService:
    @staticmethod
    def get_ticket_stats(db: Session) -> TicketStats:
        counts = dict(db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all())
        total = db.query(func.count(Ticket.id)).scalar() or 0
        needs_review = db.query(func.count(Ticket.id)).filter(Ticket.needs_review == True).scalar() or 0  # noqa: E712

        return TicketStats(
            total=total,
            open=counts.get(TicketStatusEnum.OPEN, 0),
            classified=counts.get(TicketStatusEnum.CLASSIFIED, 0),
            assigned=counts.get(TicketStatusEnum.ASSIGNED, 0),
            in_progress=counts.get(TicketStatusEnum.IN_PROGRESS, 0),
            waiting_for_user=counts.get(TicketStatusEnum.WAITING_FOR_USER, 0),
            resolved=counts.get(TicketStatusEnum.RESOLVED, 0),
            closed=counts.get(TicketStatusEnum.CLOSED, 0),
            reopened=counts.get(TicketStatusEnum.REOPENED, 0),
            needs_review=needs_review,
        )

    @staticmethod
    def get_category_distribution(db: Session) -> CategoryDistribution:
        rows = (
            db.query(Category.name, func.count(Ticket.id))
            .join(Ticket, Ticket.category_id == Category.id, isouter=True)
            .group_by(Category.name)
            .all()
        )
        return CategoryDistribution(distribution={name: count for name, count in rows})

    @staticmethod
    def get_priority_distribution(db: Session) -> PriorityDistribution:
        rows = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        return PriorityDistribution(distribution={p.value if hasattr(p, "value") else str(p): count for p, count in rows})

    @staticmethod
    def get_sla_analytics(db: Session) -> SLAAnalytics:
        # Calculate SLA breaches
        sla_breaches = db.query(func.count(Ticket.id)).filter(Ticket.sla_breached == True).scalar() or 0  # noqa: E712

        # Resolved tickets
        resolved_tickets = db.query(Ticket).filter(
            Ticket.status.in_([TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED]),
            Ticket.resolved_at.isnot(None),
        ).all()

        total_tracked = len(resolved_tickets)
        if total_tracked > 0:
            total_duration_hours = sum(
                (ensure_utc(t.resolved_at) - ensure_utc(t.created_at)).total_seconds() / 3600.0
                for t in resolved_tickets
                if t.resolved_at and t.created_at
            )
            avg_res_time = round(total_duration_hours / total_tracked, 2)
            sla_compliance = round(((total_tracked - sla_breaches) / total_tracked) * 100.0, 1)
        else:
            avg_res_time = 0.0
            sla_compliance = 100.0

        return SLAAnalytics(
            average_resolution_time_hours=avg_res_time,
            sla_breaches=sla_breaches,
            sla_compliance=max(0.0, sla_compliance),
            total_tracked=total_tracked,
        )

    @staticmethod
    def get_agent_workloads(db: Session) -> List[AgentWorkload]:
        agent_role = db.query(Role).filter(Role.name == RoleEnum.AGENT.value).first()
        if not agent_role:
            return []

        agents = db.query(User).filter(User.role_id == agent_role.id).all()
        active_statuses = [
            TicketStatusEnum.OPEN,
            TicketStatusEnum.CLASSIFIED,
            TicketStatusEnum.ASSIGNED,
            TicketStatusEnum.IN_PROGRESS,
            TicketStatusEnum.WAITING_FOR_USER,
        ]

        workloads = []
        for agent in agents:
            active_cnt = db.query(func.count(Ticket.id)).filter(
                Ticket.assigned_to == agent.id,
                Ticket.status.in_(active_statuses),
            ).scalar() or 0

            resolved_cnt = db.query(func.count(Ticket.id)).filter(
                Ticket.assigned_to == agent.id,
                Ticket.status.in_([TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED]),
            ).scalar() or 0

            dept_name = agent.department.name if agent.department else None
            workloads.append(AgentWorkload(
                agent_id=agent.id,
                agent_name=agent.name,
                department_name=dept_name,
                active_tickets=active_cnt,
                resolved_tickets=resolved_cnt,
            ))

        return workloads

    @staticmethod
    def get_ml_accuracy_stats(db: Session) -> MLAccuracyStats:
        total_predictions = db.query(func.count(TicketClassification.id)).scalar() or 0
        feedback_count = db.query(func.count(ClassificationFeedback.id)).scalar() or 0
        
        # Check how many classifications were marked correct
        correct_count = db.query(func.count(TicketClassification.id)).filter(
            TicketClassification.was_correct == True  # noqa: E712
        ).scalar() or 0

        needs_review_count = db.query(func.count(Ticket.id)).filter(Ticket.needs_review == True).scalar() or 0  # noqa: E712

        accuracy = 100.0
        if feedback_count > 0:
            accuracy = round((correct_count / feedback_count) * 100.0, 1)

        return MLAccuracyStats(
            total_predictions=total_predictions,
            feedback_collected=feedback_count,
            correct_predictions=correct_count,
            accuracy_percentage=accuracy,
            needs_review_count=needs_review_count,
        )
