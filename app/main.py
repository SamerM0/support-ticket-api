from typing import Annotated
from fastapi import FastAPI,HTTPException,status,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import engine,get_db,Base
import models
from schemas import UserCreate,UserResponse,TicketCreate,TicketResponse

# Create Tables if not found
Base.metadata.create_all(engine)

SessionDep = Annotated[Session,Depends(get_db)]

app = FastAPI()

@app.post("/users",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: SessionDep):
    # Check if username or email already exist in database
    existing_user =  db.execute(select(models.User).where(models.User.username == user.username)).scalars().first()
    if existing_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,detail="Username already exists.")

    existing_email =  db.execute(select(models.User).where(models.User.email == user.email)).scalars().first()
    if existing_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,detail="Email already exists.")

    # Create user and add to database
    new_user = models.User(username=user.username,email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.get("/users/{user_id}",response_model=UserResponse)
def get_user(user_id: int, db: SessionDep):
    user = db.execute(select(models.User).where(models.User.id == user_id)).scalars().first()
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)