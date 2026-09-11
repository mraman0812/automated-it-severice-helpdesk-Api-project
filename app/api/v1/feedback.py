import os
import csv
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.models.ticket import Ticket, PriorityEnum
from app.models.category import Category, SubCategory
from app.models.department import Department
from app.models.classification import TicketClassification, ClassificationFeedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.api.deps import get_current_user, require_roles
from app.services.audit_service import AuditService
from app.services.ticket_service import TicketService
from app.core.config import settings

router = APIRouter(prefix="/feedback", tags=["Human Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.AGENT, RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    ticket = TicketService.get_ticket_by_id(db=db, ticket_id=feedback_in.ticket_id, current_user=current_user)

    feedback = ClassificationFeedback(
        ticket_id=ticket.id,
        user_id=current_user.id,
        correct_category=feedback_in.correct_category,
        correct_subcategory=feedback_in.correct_subcategory,
        correct_priority=feedback_in.correct_priority,
        comments=feedback_in.comments,
    )
    db.add(feedback)

    # 1. Update ticket attributes with human corrections
    cat_obj = db.query(Category).filter(Category.name == feedback_in.correct_category).first()
    if cat_obj:
        ticket.category_id = cat_obj.id
        if feedback_in.correct_subcategory:
            sub_obj = db.query(SubCategory).filter(
                SubCategory.category_id == cat_obj.id,
                SubCategory.name == feedback_in.correct_subcategory,
            ).first()
            if sub_obj:
                ticket.subcategory_id = sub_obj.id

    if feedback_in.correct_priority:
        try:
            ticket.priority = PriorityEnum[feedback_in.correct_priority.upper()]
        except KeyError:
            pass

    # Human review resolved
    ticket.needs_review = False

    # 2. Update Classification history record
    latest_classification = (
        db.query(TicketClassification)
        .filter(TicketClassification.ticket_id == ticket.id)
        .order_by(TicketClassification.id.desc())
        .first()
    )
    was_correct = False
    if latest_classification:
        was_correct = (
            latest_classification.predicted_category.lower() == feedback_in.correct_category.lower()
        )
        latest_classification.was_correct = was_correct

    # 3. Active Learning: Append human-corrected ticket to training dataset
    dataset_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data", "training", "tickets.csv"
    )
    dept_name = settings.CATEGORY_DEPARTMENT_MAP.get(feedback_in.correct_category, "IT Helpdesk")
    if os.path.exists(dataset_file):
        with open(dataset_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["title", "description", "category", "subcategory", "priority", "department"]
            )
            writer.writerow({
                "title": ticket.title,
                "description": ticket.description,
                "category": feedback_in.correct_category,
                "subcategory": feedback_in.correct_subcategory or "General",
                "priority": feedback_in.correct_priority or ticket.priority.value,
                "department": dept_name,
            })

    AuditService.log_action(
        db=db,
        action="CLASSIFICATION_CORRECTED",
        entity_type="ticket",
        entity_id=ticket.ticket_number,
        user_id=current_user.id,
        details={
            "correct_category": feedback_in.correct_category,
            "correct_priority": feedback_in.correct_priority,
            "was_correct": was_correct,
        },
    )

    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("", response_model=List[FeedbackResponse])
def list_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.AGENT, RoleEnum.MANAGER, RoleEnum.ADMIN])),
):
    return db.query(ClassificationFeedback).order_by(ClassificationFeedback.id.desc()).limit(100).all()
