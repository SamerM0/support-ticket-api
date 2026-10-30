from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel

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
def get_tickets(id : int):
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

