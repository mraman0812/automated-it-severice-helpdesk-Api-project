
from typing import Optional
from sqlalchemy import Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class TicketClassification(Base, TimestampMixin):
    __tablename__ = "ticket_classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    model_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True)

    predicted_category: Mapped[str] = mapped_column(String(100), nullable=False)
    predicted_subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    predicted_priority: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    was_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="classifications")  # noqa: F821
    model: Mapped[Optional["MLModel"]] = relationship("MLModel")  # noqa: F821


class ClassificationFeedback(Base, TimestampMixin):
    __tablename__ = "classification_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    correct_category: Mapped[str] = mapped_column(String(100), nullable=False)
    correct_subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    correct_priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="feedback")  # noqa: F821
    user: Mapped["User"] = relationship("User")  # noqa: F821
