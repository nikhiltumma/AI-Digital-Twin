
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models
from .schemas import JournalEntryCreate, JournalEntryResponse, JournalExtraction
from .extraction import extract_journal


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Digital Twin API",
    description="Backend API for the AI Digital Twin project",
    version="0.3.0",
    lifespan=lifespan,
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@app.get("/")
def root():
    return {"message": "AI Digital Twin API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post(
    "/journal",
    response_model=JournalEntryResponse,
    status_code=201,
)
def create_journal(entry: JournalEntryCreate, db: DatabaseSession):
    journal = models.JournalEntry(content=entry.content)
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal


@app.get("/journal", response_model=list[JournalEntryResponse])
def list_journals(db: DatabaseSession):
    statement = select(models.JournalEntry).order_by(
        models.JournalEntry.id.desc()
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


@app.post(
    "/journal/{entry_id}/extract",
    response_model=JournalExtraction,
)
def extract_journal_entry(entry_id: int, db: DatabaseSession):
    journal = db.get(models.JournalEntry, entry_id)

    if journal is None:
        raise HTTPException(
            status_code=404,
            detail="Journal entry not found",
        )

    try:
        extraction = extract_journal(journal.content)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    statement = select(models.JournalExtractionRecord).where(
        models.JournalExtractionRecord.journal_entry_id == entry_id
    )
    record = db.scalars(statement).first()

    if record is None:
        record = models.JournalExtractionRecord(
            journal_entry_id=entry_id,
            purpose=extraction.purpose,
            actions=extraction.actions,
            deadline=extraction.deadline,
            blockers=extraction.blockers,
        )
        db.add(record)
    else:
        record.purpose = extraction.purpose
        record.actions = extraction.actions
        record.deadline = extraction.deadline
        record.blockers = extraction.blockers

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return extraction
