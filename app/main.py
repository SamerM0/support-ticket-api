from fastapi import FastAPI
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

