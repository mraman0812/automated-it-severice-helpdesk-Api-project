from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.models.ticket import Ticket
from app.models.comment import TicketComment
from app.schemas.comment import CommentCreate, CommentResponse
from app.api.deps import get_current_user
from app.services.ticket_service import TicketService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/tickets", tags=["Comments"])


@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)

    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        comment=comment_in.comment,
        is_internal=comment_in.is_internal,
    )
    db.add(comment)

    AuditService.log_action(
        db=db,
        action="COMMENT_ADDED",
        entity_type="ticket",
        entity_id=ticket.ticket_number,
        user_id=current_user.id,
        details={"comment_id": comment.id, "is_internal": comment.is_internal},
    )

    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{ticket_id}/comments", response_model=List[CommentResponse])
def get_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=ticket_id, current_user=current_user)

    query = db.query(TicketComment).filter(TicketComment.ticket_id == ticket.id)
    # If regular employee, hide internal agent notes
    role_name = current_user.role.name if current_user.role else RoleEnum.EMPLOYEE.value
    if role_name == RoleEnum.EMPLOYEE.value:
        query = query.filter(TicketComment.is_internal == False)  # noqa: E712

    return query.order_by(TicketComment.created_at.asc()).all()
