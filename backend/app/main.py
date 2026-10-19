
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models
from .schemas import (
    JournalEntryCreate,
    JournalEntryResponse,
    JournalExtraction,
    GoalCreate,
    GoalResponse,
    TaskCreate,
    TaskResponse,
)
from .extraction import extract_journal
from .schemas import ProgressResponse
from .progress import calculate_goal_progress

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.post("/goals", response_model=GoalResponse, status_code=201)
def create_goal(goal: GoalCreate, db: DatabaseSession):
    new_goal = models.Goal(
        title=goal.title.strip(),
        description=goal.description,
        target_date=goal.target_date,
        status="active",
    )

    if not new_goal.title:
        raise HTTPException(
            status_code=422,
            detail="Goal title cannot be empty",
        )

    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@app.get("/goals", response_model=list[GoalResponse])
def list_goals(db: DatabaseSession):
    statement = select(models.Goal).order_by(models.Goal.id.desc())
    return db.scalars(statement).all()


@app.get("/goals/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: int, db: DatabaseSession):
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    return goal


@app.post(
    "/goals/{goal_id}/tasks",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    goal_id: int,
    task: TaskCreate,
    db: DatabaseSession,
):
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    title = task.title.strip()

    if not title:
        raise HTTPException(
            status_code=422,
            detail="Task title cannot be empty",
        )

    new_task = models.Task(
        goal_id=goal_id,
        title=title,
        completed=False,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@app.get(
    "/goals/{goal_id}/tasks",
    response_model=list[TaskResponse],
)
def list_tasks(goal_id: int, db: DatabaseSession):
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    statement = (
        select(models.Task)
        .where(models.Task.goal_id == goal_id)
        .order_by(models.Task.id.asc())
    )

    return db.scalars(statement).all()


@app.patch("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int, db: DatabaseSession):
    task = db.get(models.Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    task.completed = True

    db.commit()
    db.refresh(task)

    return task


@app.post(
    "/goals/{goal_id}/progress",
    response_model=ProgressResponse,
    status_code=201,
)
def create_progress_snapshot(
    goal_id: int,
    db: DatabaseSession,
):
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    progress_data = calculate_goal_progress(db, goal_id)

    snapshot = models.Progress(
        goal_id=goal_id,
        completed_tasks=progress_data["completed_tasks"],
        total_tasks=progress_data["total_tasks"],
        percentage=progress_data["percentage"],
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot
