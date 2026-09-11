from typing import Optional, List
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role: Mapped["Role"] = relationship("Role", back_populates="users")  # noqa: F821
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="users")  # noqa: F821

    created_tickets: Mapped[List["Ticket"]] = relationship(  # noqa: F821
        "Ticket",
        foreign_keys="[Ticket.created_by]",
        back_populates="creator",
    )
    assigned_tickets: Mapped[List["Ticket"]] = relationship(  # noqa: F821
        "Ticket",
        foreign_keys="[Ticket.assigned_to]",
        back_populates="assignee",
    )
    comments: Mapped[List["TicketComment"]] = relationship("TicketComment", back_populates="user")  # noqa: F821
