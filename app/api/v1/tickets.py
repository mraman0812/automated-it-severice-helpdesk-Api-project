from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketAssign,
    TicketResolve,
    TicketResponse,
    TicketListResponse,
)
from app.api.deps import get_current_user, require_roles
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.create_ticket(db=db, user=current_user, ticket_in=ticket_in)
    return TicketService.format_ticket_response(ticket)


@router.get("", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    department_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    needs_review: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total, total_pages = TicketService.get_tickets(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        category_id=category_id,
        department_id=department_id,
        assigned_to=assigned_to,
        needs_review=needs_review,
        search=search,
    )
    formatted_items = [TicketService.format_ticket_response(t) for t in items]
    return TicketListResponse(
        items=formatted_items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/search", response_model=TicketListResponse)
def search_tickets(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total, total_pages = TicketService.get_tickets(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        search=q,
    )
    formatted_items = [TicketService.format_ticket_response(t) for t in items]
    return TicketListResponse(
        items=formatted_items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)
    return TicketService.format_ticket_response(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)
    updated = TicketService.update_ticket(db=db, ticket=ticket, update_data=ticket_update, current_user=current_user)
    return TicketService.format_ticket_response(updated)


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket(
    ticket_id: int,
    assign_in: TicketAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.AGENT, RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)
    assigned = TicketService.assign_ticket(db=db, ticket=ticket, agent_id=assign_in.agent_id, current_user=current_user)
    return TicketService.format_ticket_response(assigned)


@router.post("/{ticket_id}/resolve", response_model=TicketResponse)
def resolve_ticket(
    ticket_id: int,
    resolve_in: TicketResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.AGENT, RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)
    resolved = TicketService.resolve_ticket(
        db=db, ticket=ticket, resolution=resolve_in.resolution, current_user=current_user
    )
    return TicketService.format_ticket_response(resolved)


@router.post("/{ticket_id}/close", response_model=TicketResponse)
def close_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)
    closed = TicketService.close_ticket(db=db, ticket=ticket, current_user=current_user)
    return TicketService.format_ticket_response(closed)


@router.post("/{ticket_id}/reopen", response_model=TicketResponse)
def reopen_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)
    reopened = TicketService.reopen_ticket(db=db, ticket=ticket, current_user=current_user)
    return TicketService.format_ticket_response(reopened)
