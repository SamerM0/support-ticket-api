from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app import models
from app.dependencies import SessionDep
from app.enums import UserRole
from app.schemas import (
    MessageCreate,
    MessageResponse,
    TicketAssign,
    TicketCreate,
    TicketResponse,
    TicketStatusUpdate,
)

router = APIRouter()


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/{ticket_id}", response_model=TicketResponse)
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


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
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


@router.patch("/{ticket_id}/assign", response_model=TicketResponse)
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
    if ticket_data.agent_id is not None:
        result = await db.execute(
            select(models.User).where(models.User.id == ticket_data.agent_id)
        )
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )
        if user.role != UserRole.AGENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an agent."
            )

    ticket.agent_id = ticket_data.agent_id
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.post(
    "/{ticket_id}/messages",
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
@router.get("/{ticket_id}/messages", response_model=list[MessageResponse])
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
