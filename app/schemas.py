from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from enums import TicketStatus, UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole

class TicketBase(BaseModel):
    title: str
    content: str
    customer_id: int

class TicketCreate(TicketBase):
    pass

class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TicketStatus
    date_created: datetime
    agent_id: int | None = None