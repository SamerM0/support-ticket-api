from __future__ import annotations

from datetime import UTC, datetime

from database import Base
from enums import TicketStatus, UserRole
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)

    role: Mapped[UserRole] = mapped_column(default=UserRole.CUSTOMER)

    created_tickets: Mapped[list[Ticket]] = relationship(
        back_populates="customer", foreign_keys="Ticket.customer_id"
    )
    assigned_tickets: Mapped[list[Ticket]] = relationship(
        back_populates="agent", foreign_keys="Ticket.agent_id"
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    content: Mapped[str]
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.OPEN)
    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    customer: Mapped[User] = relationship(
        back_populates="created_tickets", foreign_keys=[customer_id]
    )
    agent: Mapped[User | None] = relationship(
        back_populates="assigned_tickets", foreign_keys=[agent_id]
    )
