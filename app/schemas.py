from datetime import datetime

from enums import TicketStatus, UserRole
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- User Schemas ----------
class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=20)
    email: EmailStr = Field(min_length=1, max_length=80)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole


class UserUpdateData(BaseModel):
    username: str | None = Field(min_length=1, max_length=20, default=None)
    email: EmailStr | None = Field(min_length=1, max_length=80, default=None)


class UserUpdateRole(BaseModel):
    role: UserRole


# ---------- Ticket Schemas ----------
class TicketBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    customer_id: int


class TicketCreate(TicketBase):
    pass


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketAssign(BaseModel):
    agent_id: int | None


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TicketStatus
    date_created: datetime
    agent_id: int | None = None


# ---------- Message Schemas ----------
class MessageBase(BaseModel):
    content: str = Field(min_length=1)
    author_id: int


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_created: datetime
