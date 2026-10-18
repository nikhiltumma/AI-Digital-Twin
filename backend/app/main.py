from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models
from .schemas import JournalEntryCreate, JournalEntryResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Digital Twin API",
    description="Backend API for the AI Digital Twin project",
    version="0.2.0",
    lifespan=lifespan,
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@app.get("/")
def root():
    return {"message": "AI Digital Twin API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/journal", response_model=JournalEntryResponse, status_code=201)
def create_journal(
    entry: JournalEntryCreate,
    db: DatabaseSession,
):
    journal = models.JournalEntry(content=entry.content)

    db.add(journal)
    db.commit()
    db.refresh(journal)

    return journal


@app.get("/journal", response_model=list[JournalEntryResponse])
def list_journals(db: DatabaseSession):
    statement = (
        select(models.JournalEntry)
        .order_by(models.JournalEntry.id.desc())
    )
    return db.scalars(statement).all()


@app.get("/journal/{entry_id}", response_model=JournalEntryResponse)
def get_journal(entry_id: int, db: DatabaseSession):
    journal = db.get(models.JournalEntry, entry_id)

    if journal is None:
        raise HTTPException(
            status_code=404,
            detail="Journal entry not found",
        )

    return journal