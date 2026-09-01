from sqlmodel import SQLModel, create_engine, Session, select
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./academic_assistant.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

from models.quiz import QuizAttempt
from models.processed_document import ProcessedDocument

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session