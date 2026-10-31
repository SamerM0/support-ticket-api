from sqlalchemy.orm import Mapped,mapped_column
from database import Base
from enums import TicketStatus

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] 
    content: Mapped[str] 
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.OPEN)