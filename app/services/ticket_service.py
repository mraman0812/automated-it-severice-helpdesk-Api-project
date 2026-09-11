import math
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import or_, and_, desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundException, ForbiddenException, HelpdeskException
from app.models.ticket import Ticket, PriorityEnum, TicketStatusEnum
from app.models.user import User
from app.models.role import RoleEnum
from app.models.category import Category, SubCategory
from app.models.department import Department
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketClassificationSummary
from app.services.classification_service import ClassificationService
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TicketService:
    @staticmethod
    def generate_ticket_number(db: Session) -> str:
        year = datetime.now(timezone.utc).year
        # Count tickets created this year
        count = db.query(func.count(Ticket.id)).scalar() or 0
        return f"IT-{year}-{count + 1:06d}"

    @staticmethod
    def calculate_sla_deadline(priority: str) -> datetime:
        hours = settings.SLA_HOURS.get(priority.upper(), 24)
        return datetime.now(timezone.utc) + timedelta(hours=hours)

    @classmethod
    def create_ticket(cls, db: Session, user: User, ticket_in: TicketCreate) -> Ticket:
        ticket_number = cls.generate_ticket_number(db)

        # 1. Run ML classification
        prediction = ClassificationService.predict_ticket(ticket_in.title, ticket_in.description, db=db)

        predicted_priority = prediction["priority"]
        try:
            priority_enum = PriorityEnum[predicted_priority]
        except KeyError:
            priority_enum = PriorityEnum.MEDIUM

        sla_deadline = cls.calculate_sla_deadline(predicted_priority)

        # 2. Workload-balanced agent assignment
        assigned_agent = None
        department_id = prediction["department_id"]
        if department_id:
            assigned_agent = AssignmentService.assign_agent(db, department_id)

        # Determine initial status
        if assigned_agent:
            initial_status = TicketStatusEnum.ASSIGNED
        elif prediction["needs_review"]:
            initial_status = TicketStatusEnum.OPEN
        else:
            initial_status = TicketStatusEnum.CLASSIFIED

        ticket = Ticket(
            ticket_number=ticket_number,
            title=ticket_in.title,
            description=ticket_in.description,
            created_by=user.id,
            category_id=prediction["category_id"],
            subcategory_id=prediction["subcategory_id"],
            department_id=department_id,
            priority=priority_enum,
            status=initial_status,
            assigned_to=assigned_agent.id if assigned_agent else None,
            predicted_category=prediction["category"],
            predicted_subcategory=prediction["subcategory"],
            predicted_priority=prediction["priority"],
            confidence_score=prediction["confidence"],
            needs_review=prediction["needs_review"],
            sla_deadline=sla_deadline,
            sla_breached=False,
        )

        db.add(ticket)
        db.flush()

        # Save classification record with the newly generated ticket.id
        ClassificationService.predict_ticket(
            ticket_in.title,
            ticket_in.description,
            db=db,
            ticket_id=ticket.id,
        )

        AuditService.log_action(
            db=db,
            action="TICKET_CREATED",
            entity_type="ticket",
            entity_id=ticket.ticket_number,
            user_id=user.id,
            details={
                "title": ticket.title,
                "category": prediction["category"],
                "priority": str(priority_enum.value),
                "assigned_to": ticket.assigned_to,
                "confidence": prediction["confidence"],
            },
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    @classmethod
    def get_tickets(
        cls,
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category_id: Optional[int] = None,
        department_id: Optional[int] = None,
        assigned_to: Optional[int] = None,
        needs_review: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Ticket], int, int]:
        query = db.query(Ticket)

        # RBAC Filtering
        role_name = current_user.role.name if current_user.role else RoleEnum.EMPLOYEE.value
        if role_name == RoleEnum.EMPLOYEE.value:
            query = query.filter(Ticket.created_by == current_user.id)
        elif role_name == RoleEnum.AGENT.value:
            # Agents see tickets assigned to them, or unassigned in their department, or can filter
            if assigned_to:
                query = query.filter(Ticket.assigned_to == assigned_to)
            elif current_user.department_id:
                query = query.filter(
                    or_(
                        Ticket.assigned_to == current_user.id,
                        and_(Ticket.department_id == current_user.department_id, Ticket.assigned_to.is_(None)),
                    )
                )

        # Apply specific filters
        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        if category_id:
            query = query.filter(Ticket.category_id == category_id)
        if department_id:
            query = query.filter(Ticket.department_id == department_id)
        if assigned_to and role_name in [RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]:
            query = query.filter(Ticket.assigned_to == assigned_to)
        if needs_review is not None:
            query = query.filter(Ticket.needs_review == needs_review)

        # Text search
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Ticket.ticket_number.ilike(search_pattern),
                    Ticket.title.ilike(search_pattern),
                    Ticket.description.ilike(search_pattern),
                    Ticket.predicted_category.ilike(search_pattern),
                )
            )

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(desc(Ticket.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        # Check SLA breach status dynamically
        now = datetime.now(timezone.utc)
        for t in items:
            if t.status not in [TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED]:
                if t.sla_deadline and ensure_utc(t.sla_deadline) < now:
                    t.sla_breached = True

        return items, total, total_pages

    @classmethod
    def get_ticket_by_id(cls, db: Session, ticket_id: int, current_user: User) -> Ticket:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise NotFoundException(f"Ticket #{ticket_id} not found", error_code="TICKET_NOT_FOUND")

        # RBAC check
        role_name = current_user.role.name if current_user.role else RoleEnum.EMPLOYEE.value
        if role_name == RoleEnum.EMPLOYEE.value and ticket.created_by != current_user.id:
            raise ForbiddenException("You do not have permission to view this ticket")

        # SLA breach dynamic evaluation
        now = datetime.now(timezone.utc)
        if ticket.status not in [TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED]:
            if ticket.sla_deadline and ensure_utc(ticket.sla_deadline) < now:
                ticket.sla_breached = True

        return ticket

    @classmethod
    def update_ticket(cls, db: Session, ticket: Ticket, update_data: TicketUpdate, current_user: User) -> Ticket:
        role_name = current_user.role.name if current_user.role else RoleEnum.EMPLOYEE.value
        if role_name == RoleEnum.EMPLOYEE.value and ticket.created_by != current_user.id:
            raise ForbiddenException("You do not have permission to update this ticket")

        changes = {}
        for field, value in update_data.model_dump(exclude_unset=True).items():
            old_val = getattr(ticket, field)
            if old_val != value:
                changes[field] = {"old": str(old_val), "new": str(value)}
                setattr(ticket, field, value)

        if "priority" in changes:
            ticket.sla_deadline = cls.calculate_sla_deadline(ticket.priority.value)

        AuditService.log_action(
            db=db,
            action="TICKET_UPDATED",
            entity_type="ticket",
            entity_id=ticket.ticket_number,
            user_id=current_user.id,
            details=changes,
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    @classmethod
    def assign_ticket(cls, db: Session, ticket: Ticket, agent_id: int, current_user: User) -> Ticket:
        agent = db.query(User).filter(User.id == agent_id).first()
        if not agent:
            raise NotFoundException("Agent not found", error_code="AGENT_NOT_FOUND")

        old_assignee = ticket.assigned_to
        ticket.assigned_to = agent.id
        if ticket.status in [TicketStatusEnum.OPEN, TicketStatusEnum.CLASSIFIED]:
            ticket.status = TicketStatusEnum.ASSIGNED

        AuditService.log_action(
            db=db,
            action="TICKET_ASSIGNED",
            entity_type="ticket",
            entity_id=ticket.ticket_number,
            user_id=current_user.id,
            details={"old_assignee": old_assignee, "new_assignee": agent.id, "agent_name": agent.name},
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    @classmethod
    def resolve_ticket(cls, db: Session, ticket: Ticket, resolution: str, current_user: User) -> Ticket:
        role_name = current_user.role.name if current_user.role else RoleEnum.EMPLOYEE.value
        if role_name == RoleEnum.EMPLOYEE.value:
            raise ForbiddenException("Employees cannot resolve tickets directly")

        now = datetime.now(timezone.utc)
        ticket.status = TicketStatusEnum.RESOLVED
        ticket.resolution_note = resolution
        ticket.resolved_at = now

        if ticket.sla_deadline and ensure_utc(ticket.resolved_at) > ensure_utc(ticket.sla_deadline):
            ticket.sla_breached = True

        AuditService.log_action(
            db=db,
            action="TICKET_RESOLVED",
            entity_type="ticket",
            entity_id=ticket.ticket_number,
            user_id=current_user.id,
            details={"resolution": resolution, "sla_breached": ticket.sla_breached},
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    @classmethod
    def close_ticket(cls, db: Session, ticket: Ticket, current_user: User) -> Ticket:
        ticket.status = TicketStatusEnum.CLOSED
        ticket.closed_at = datetime.now(timezone.utc)

        AuditService.log_action(
            db=db,
            action="TICKET_CLOSED",
            entity_type="ticket",
            entity_id=ticket.ticket_number,
            user_id=current_user.id,
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    @classmethod
    def reopen_ticket(cls, db: Session, ticket: Ticket, current_user: User) -> Ticket:
        ticket.status = TicketStatusEnum.REOPENED
        ticket.resolved_at = None
        ticket.closed_at = None
        ticket.resolution_note = None

        AuditService.log_action(
            db=db,
            action="TICKET_REOPENED",
            entity_type="ticket",
            entity_id=ticket.ticket_number,
            user_id=current_user.id,
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def format_ticket_response(ticket: Ticket) -> TicketResponse:
        classification_summary = TicketClassificationSummary(
            category=ticket.predicted_category or (ticket.category.name if ticket.category else None),
            subcategory=ticket.predicted_subcategory or (ticket.subcategory.name if ticket.subcategory else None),
            priority=ticket.predicted_priority or ticket.priority.value,
            confidence=ticket.confidence_score or 0.0,
        )

        dept_name = ticket.department.name if ticket.department else None
        cat_name = ticket.category.name if ticket.category else None
        subcat_name = ticket.subcategory.name if ticket.subcategory else None

        return TicketResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status.value,
            priority=ticket.priority.value,
            department_id=ticket.department_id,
            department_name=dept_name,
            category_id=ticket.category_id,
            category_name=cat_name,
            subcategory_id=ticket.subcategory_id,
            subcategory_name=subcat_name,
            created_by=ticket.created_by,
            assigned_to=ticket.assigned_to,
            creator=ticket.creator,
            assignee=ticket.assignee,
            department=ticket.department,
            classification=classification_summary,
            confidence_score=ticket.confidence_score or 0.0,
            needs_review=ticket.needs_review,
            sla_deadline=ticket.sla_deadline,
            sla_breached=ticket.sla_breached,
            resolution_note=ticket.resolution_note,
            resolved_at=ticket.resolved_at,
            closed_at=ticket.closed_at,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )
