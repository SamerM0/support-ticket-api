from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app import models
from app.dependencies import SessionDep
from app.schemas import (
    TicketResponse,
    UserCreate,
    UserResponse,
    UserUpdateData,
    UserUpdateRole,
)

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: SessionDep):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
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


@router.patch("/{user_id}/role", response_model=UserResponse)
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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
@router.get("/{user_id}/tickets", response_model=list[TicketResponse])
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
