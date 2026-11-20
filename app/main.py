from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import tickets, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create async connection and create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield  # App running
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="/users", tags=["users"])

app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
