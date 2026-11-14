from __future__ import annotations
from datetime import datetime,UTC
from sqlalchemy import ForeignKey,DateTime
from sqlalchemy.orm import Mapped,mapped_column,relationship
from database import Base
from enums import TicketStatus,UserRole

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True,index=True)
    username: Mapped[str] = mapped_column(unique=True,nullable=False)
    email: Mapped[str] = mapped_column(unique=True,nullable=False)

    role: Mapped[UserRole] = mapped_column(default=UserRole.CUSTOMER)

    created_tickets: Mapped[list[Ticket]] = relationship(back_populates="customer")
    assigned_tickets: Mapped[list[Ticket]] = relationship(back_populates="agent")

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    title: Mapped[str] 
    content: Mapped[str] 
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False)
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.OPEN)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(UTC))

    customer: Mapped[User] = relationship(back_populates="created_tickets")
    agent: Mapped[User] = relationship(back_populates="assigned_tickets")
