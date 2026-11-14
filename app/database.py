import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"],echo=True,pool_pre_ping=True)

SessionLocal = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as session:
        yield session