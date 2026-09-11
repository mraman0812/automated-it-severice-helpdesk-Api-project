import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class PriorityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    CLASSIFIED = "CLASSIFIED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    subcategory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("subcategories.id"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)

    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum, native_enum=False),
        default=PriorityEnum.MEDIUM,
        nullable=False,
        index=True,
    )
    status: Mapped[TicketStatusEnum] = mapped_column(
        Enum(TicketStatusEnum, native_enum=False),
        default=TicketStatusEnum.OPEN,
        nullable=False,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # ML Prediction fields
    predicted_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    predicted_subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    predicted_priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # SLA tracking
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by], back_populates="created_tickets")  # noqa: F821
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tickets")  # noqa: F821
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="tickets")  # noqa: F821
    subcategory: Mapped[Optional["SubCategory"]] = relationship("SubCategory", back_populates="tickets")  # noqa: F821
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="tickets")  # noqa: F821

    comments: Mapped[List["TicketComment"]] = relationship(  # noqa: F821
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketComment.created_at.asc()",
    )
    attachments: Mapped[List["TicketAttachment"]] = relationship(  # noqa: F821
        "TicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    classifications: Mapped[List["TicketClassification"]] = relationship(  # noqa: F821
        "TicketClassification",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[List["ClassificationFeedback"]] = relationship(  # noqa: F821
        "ClassificationFeedback",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
