from sqlalchemy import text
from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel
from database import engine,SessionLocal,Base
import models

# Create Table if not found
Base.metadata.create_all(engine)

app = FastAPI()

class TicketCreate(BaseModel):
    title: str
    content: str

tickets = {}
next_id = 1

@app.get("/tickets")
def get_tickets():
    return tickets

@app.get("/tickets/{id}")
def get_ticket(id : int):
    if id not in tickets:
        raise HTTPException(status.HTTP_404_NOT_FOUND,f"Ticket with id {id} not found.")
    return tickets[id]

@app.post("/tickets")
def create_ticket(ticket : TicketCreate):
    global next_id

    tickets[next_id] = {
        "id":next_id,
        "title":ticket.title,
        "content":ticket.content
        }
    
    next_id += 1
    return tickets[next_id-1]

