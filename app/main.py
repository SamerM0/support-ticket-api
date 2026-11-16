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
from sqlalchemy.orm import Session

# Create Tables if not found
Base.metadata.create_all(engine)

SessionDep = Annotated[Session, Depends(get_db)]

app = FastAPI()


# ---------- User Endpoints ----------
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: SessionDep):
    # Check if username or email already exist in database
    existing_user = (
        db.execute(select(models.User).where(models.User.username == user.username))
        .scalars()
        .first()
    )
    if existing_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Username already exists."
        )

    existing_email = (
        db.execute(select(models.User).where(models.User.email == user.email))
        .scalars()
        .first()
    )
    if existing_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Email already exists.")

    # Create user and add to database
    new_user = models.User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: SessionDep):
    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )
    if user:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )


@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdateData, db: SessionDep):
    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if user_data.username is not None and user_data.username != user.username:
        existing_username = (
            db.execute(
                select(models.User).where(models.User.username == user_data.username)
            )
            .scalars()
            .first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists.",
            )

    if user_data.email is not None and user_data.email != user.email:
        existing_email = (
            db.execute(select(models.User).where(models.User.email == user_data.email))
            .scalars()
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists.",
            )

    new_data = user_data.model_dump(exclude_none=True, exclude_unset=True)

    for field, value in new_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@app.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: int, user_role: UserUpdateRole, db: SessionDep):
    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    user.role = user_role.role
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: SessionDep):
    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )
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
    db.delete(user)
    db.commit()


# Get user tickets
@app.get("/users/{user_id}/tickets", response_model=list[TicketResponse])
def get_user_tickets(user_id: int, db: SessionDep):
    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    return user.created_tickets


# ---------- Ticket Endpoints ----------
@app.post(
    "/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED
)
def create_ticket(ticket: TicketCreate, db: SessionDep):
    # Check if user exists
    user = (
        db.execute(select(models.User).where(models.User.id == ticket.customer_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # Create ticket and add to database
    new_ticket = models.Ticket(
        title=ticket.title, content=ticket.content, customer_id=ticket.customer_id
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: SessionDep):
    ticket = (
        db.execute(select(models.Ticket).where(models.Ticket.id == ticket_id))
        .scalars()
        .first()
    )
    if ticket:
        return ticket
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )


@app.patch("/tickets/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(
    ticket_id: int, ticket_data: TicketStatusUpdate, db: SessionDep
):
    ticket = (
        db.execute(select(models.Ticket).where(models.Ticket.id == ticket_id))
        .scalars()
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )

    ticket.status = ticket_data.status
    db.commit()
    db.refresh(ticket)
    return ticket


@app.patch("/tickets/{ticket_id}/assign", response_model=TicketResponse)
def update_ticket_agent(ticket_id: int, ticket_data: TicketAssign, db: SessionDep):
    ticket = (
        db.execute(select(models.Ticket).where(models.Ticket.id == ticket_id))
        .scalars()
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )
    user = (
        db.execute(select(models.User).where(models.User.id == ticket_data.agent_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    ticket.agent_id = ticket_data.agent_id
    db.commit()
    db.refresh(ticket)
    return ticket


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: SessionDep):
    ticket = (
        db.execute(select(models.Ticket).where(models.Ticket.id == ticket_id))
        .scalars()
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )

    db.delete(ticket)
    db.commit()


# ---------- Message endpoints ----------
@app.post(
    "/tickets/{ticket_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_message(message: MessageCreate, ticket_id: int, db: SessionDep):
    ticket = (
        db.execute(select(models.Ticket).where(models.Ticket.id == ticket_id))
        .scalars()
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )

    user = (
        db.execute(select(models.User).where(models.User.id == message.author_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # Create message and add to database
    new_message = models.Message(
        content=message.content, ticket_id=ticket_id, author_id=message.author_id
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return new_message


# Get ticket messages
@app.get("/tickets/{ticket_id}/messages", response_model=list[MessageResponse])
def get_ticket_messages(ticket_id: int, db: SessionDep):
    ticket = (
        db.execute(select(models.Ticket).where(models.Ticket.id == ticket_id))
        .scalars()
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )
    return ticket.messages
