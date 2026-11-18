from contextlib import asynccontextmanager
from typing import Annotated

import models
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException, status
from schemas import (
    MessageCreate,
    MessageResponse,
    TicketAssign,
    TicketCreate,
    TicketResponse,
    TicketStatusUpdate,
    UserCreate,
    UserResponse,
    UserUpdateData,
    UserUpdateRole,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create async connection and create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield  # App running
    # Shutdown
    await engine.dispose()


SessionDep = Annotated[AsyncSession, Depends(get_db)]

app = FastAPI(lifespan=lifespan)


# ---------- User Endpoints ----------
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: SessionDep):
    # Check if username or email already exist in database
    result = await db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Username already exists."
        )

    result = await db.execute(
        select(models.User).where(models.User.email == user.email)
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Email already exists.")

    # Create user and add to database
    new_user = models.User(username=user.username, email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: SessionDep):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    return user


@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdateData, db: SessionDep):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if user_data.username is not None and user_data.username != user.username:
        result = await db.execute(
            select(models.User).where(models.User.username == user_data.username)
        )
        existing_username = result.scalars().first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists.",
            )

    if user_data.email is not None and user_data.email != user.email:
        result = await db.execute(
            select(models.User).where(models.User.email == user_data.email)
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists.",
            )

    new_data = user_data.model_dump(exclude_none=True, exclude_unset=True)

    for field, value in new_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@app.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(user_id: int, user_role: UserUpdateRole, db: SessionDep):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    user.role = user_role.role
    await db.commit()
    await db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: SessionDep):
    result = await db.execute(
        select(models.User)
        .options(
            selectinload(models.User.created_tickets),
            selectinload(models.User.assigned_tickets),
            selectinload(models.User.messages),
        )
        .where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    if user.created_tickets or user.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has tickets or messages.",
        )
    for ticket in user.assigned_tickets:
        ticket.agent_id = None
    await db.delete(user)
    await db.commit()


# Get user tickets
@app.get("/users/{user_id}/tickets", response_model=list[TicketResponse])
async def get_user_tickets(user_id: int, db: SessionDep):
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.created_tickets))
        .where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    return user.created_tickets


# ---------- Ticket Endpoints ----------
@app.post(
    "/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED
)
async def create_ticket(ticket: TicketCreate, db: SessionDep):
    # Check if user exists
    result = await db.execute(
        select(models.User).where(models.User.id == ticket.customer_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # Create ticket and add to database
    new_ticket = models.Ticket(
        title=ticket.title, content=ticket.content, customer_id=ticket.customer_id
    )
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)

    return new_ticket


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: SessionDep):
    result = await db.execute(
        select(models.Ticket).where(models.Ticket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )
    return ticket


@app.patch("/tickets/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: int, ticket_data: TicketStatusUpdate, db: SessionDep
):
    result = await db.execute(
        select(models.Ticket).where(models.Ticket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )

    ticket.status = ticket_data.status
    await db.commit()
    await db.refresh(ticket)
    return ticket


@app.patch("/tickets/{ticket_id}/assign", response_model=TicketResponse)
async def update_ticket_agent(
    ticket_id: int, ticket_data: TicketAssign, db: SessionDep
):
    result = await db.execute(
        select(models.Ticket).where(models.Ticket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )
    result = await db.execute(
        select(models.User).where(models.User.id == ticket_data.agent_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    ticket.agent_id = ticket_data.agent_id
    await db.commit()
    await db.refresh(ticket)
    return ticket


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(ticket_id: int, db: SessionDep):
    result = await db.execute(
        select(models.Ticket).where(models.Ticket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )

    await db.delete(ticket)
    await db.commit()


# ---------- Message endpoints ----------
@app.post(
    "/tickets/{ticket_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(message: MessageCreate, ticket_id: int, db: SessionDep):
    result = await db.execute(
        select(models.Ticket).where(models.Ticket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )

    result = await db.execute(
        select(models.User).where(models.User.id == message.author_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # Create message and add to database
    new_message = models.Message(
        content=message.content, ticket_id=ticket_id, author_id=message.author_id
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return new_message


# Get ticket messages
@app.get("/tickets/{ticket_id}/messages", response_model=list[MessageResponse])
async def get_ticket_messages(ticket_id: int, db: SessionDep):
    result = await db.execute(
        select(models.Ticket)
        .options(selectinload(models.Ticket.messages))
        .where(models.Ticket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )
    return ticket.messages
