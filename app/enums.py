from enum import StrEnum

class UserRole(StrEnum):
  CUSTOMER = "customer"
  AGENT = "agent"

class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

