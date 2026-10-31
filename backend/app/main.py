
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    UploadFile,
    File,
)
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models
from .planning import generate_plan

from .schemas import (
    JournalEntryCreate,
    JournalEntryResponse,
    JournalExtraction,
    GoalDocumentResponse,
    GoalCreate,
    GoalResponse,
    TaskCreate,
    TaskResponse,
    ProgressResponse,
)

from .document_storage import (
    DOCUMENT_STORAGE_DIR,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
)

from .extraction import extract_journal
from .progress import calculate_goal_progress


# Database dependency
DatabaseSession = Annotated[Session, Depends(get_db)]


# Application lifespan
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


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
def root():
    return {"message": "AI Digital Twin API is running"}


# Health endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# JOURNAL ENDPOINTS
# --------------------------------------------------

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


@app.get(
    "/journal",
    response_model=list[JournalEntryResponse],
)
def list_journals(db: DatabaseSession):
    statement = select(models.JournalEntry).order_by(
        models.JournalEntry.id.desc()
    )

    return db.scalars(statement).all()


@app.get(
    "/journal/{entry_id}",
    response_model=JournalEntryResponse,
)
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

    statement = select(
        models.JournalExtractionRecord
    ).where(
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


# --------------------------------------------------
# GOAL ENDPOINTS
# --------------------------------------------------

@app.post(
    "/goals",
    response_model=GoalResponse,
    status_code=201,
)
def create_goal(goal: GoalCreate, db: DatabaseSession):
    new_goal = models.Goal(
        title=goal.title.strip(),
        domain=goal.domain.strip().lower(),
        description=goal.description,
        current_state=goal.current_state,
        target_state=goal.target_state,
        timeline_value=goal.timeline_value,
        timeline_unit=goal.timeline_unit,
        resources=goal.resources,
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


@app.get(
    "/goals",
    response_model=list[GoalResponse],
)
def list_goals(db: DatabaseSession):
    statement = select(models.Goal).order_by(
        models.Goal.id.desc()
    )

    return db.scalars(statement).all()


@app.get(
    "/goals/{goal_id}",
    response_model=GoalResponse,
)
def get_goal(goal_id: int, db: DatabaseSession):
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    return goal


# --------------------------------------------------
# TASK ENDPOINTS
# --------------------------------------------------

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


@app.patch(
    "/tasks/{task_id}/complete",
    response_model=TaskResponse,
)
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


# --------------------------------------------------
# PROGRESS ENDPOINT
# --------------------------------------------------

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


# --------------------------------------------------
# DOCUMENT UPLOAD ENDPOINT
# --------------------------------------------------

@app.post(
    "/goals/{goal_id}/documents",
    response_model=GoalDocumentResponse,
    status_code=201,
)
async def upload_goal_document(
    goal_id: int,
    db: DatabaseSession,
    file: UploadFile = File(...),
):
    # 1. Verify that the goal exists
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    # 2. Validate filename and extension
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()

    if not original_name or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format",
        )

    # 3. Validate MIME type
    allowed_mime_types = {
        ".pdf": {"application/pdf"},
        ".docx": {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        },
        ".xlsx": {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        },
        ".txt": {"text/plain"},
    }

    if file.content_type not in allowed_mime_types[extension]:
        raise HTTPException(
            status_code=400,
            detail="File content type does not match the file extension",
        )

    # 4. Read and validate file size
    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MB limit",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Empty files are not allowed",
        )

    # 5. Generate a unique server-side filename
    stored_name = f"{uuid.uuid4().hex}{extension}"
    storage_path = DOCUMENT_STORAGE_DIR / stored_name

    try:
        # 6. Save physical file
        storage_path.write_bytes(content)

        # 7. Save metadata in PostgreSQL
        document = models.GoalDocument(
            goal_id=goal_id,
            file_name=original_name,
            file_type=file.content_type,
            file_size=len(content),
            storage_path=str(storage_path),
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()

        # Delete physical file if database operation fails
        storage_path.unlink(missing_ok=True)

        raise

    finally:
        await file.close()


@app.get(
    "/goals/{goal_id}/documents",
    response_model=list[GoalDocumentResponse],
)
def list_goal_documents(
    goal_id: int,
    db: DatabaseSession,
):
    # 1. Verify that the goal exists
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    # 2. Retrieve documents associated with this goal
    statement = (
        select(models.GoalDocument)
        .where(models.GoalDocument.goal_id == goal_id)
        .order_by(models.GoalDocument.uploaded_at.desc())
    )

    documents = db.scalars(statement).all()

    return documents



@app.post(
    "/goals/{goal_id}/generate-plan",
    status_code=201,
)
def create_ai_plan(
    goal_id: int,
    db: DatabaseSession,
):
    # 1. Fetch the goal
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    # 2. Prepare goal information
    goal_data = {
        "domain": goal.domain,
        "title": goal.title,
        "description": goal.description,
        "current_state": goal.current_state,
        "target_state": goal.target_state,
        "timeline_value": goal.timeline_value,
        "timeline_unit": goal.timeline_unit,
        "resources": goal.resources,
    }

    # 3. Generate AI plan
    try:
        generated_plan = generate_plan(goal_data)

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # 4. Validate and extract activities
    milestones = generated_plan.get("milestones", [])

    if not isinstance(milestones, list):
        raise HTTPException(
            status_code=502,
            detail="Invalid milestones returned by AI",
        )

    task_titles = []

    for milestone in milestones:
        if not isinstance(milestone, dict):
            continue

        weekly_targets = milestone.get("weekly_targets", [])

        if not isinstance(weekly_targets, list):
            continue

        for weekly_target in weekly_targets:
            if not isinstance(weekly_target, dict):
                continue

            week = weekly_target.get("week", "")
            tasks = weekly_target.get("tasks", [])

            if not isinstance(tasks, list):
                continue

            for task_title in tasks:
                if not isinstance(task_title, str) or not task_title.strip():
                    continue

                formatted_title = (
                    f"Month {milestone.get('month', '?')} "
                    f"- Week {week}: {task_title.strip()}"
                )

                task_titles.append(formatted_title)

    if not task_titles:
        raise HTTPException(
            status_code=502,
            detail="AI generated no valid tasks",
        )

    # 5. Create plan and task records
    new_plan = models.Plan(
        goal_id=goal_id,
        summary=generated_plan["summary"],
        plan_data=generated_plan,
        version=1,
    )

    try:
        db.add(new_plan)

        for title in task_titles:
            new_task = models.Task(
                goal_id=goal_id,
                title=title,
                completed=False,
            )
            db.add(new_task)

        db.commit()
        db.refresh(new_plan)

    except Exception:
        db.rollback()
        raise

    # 6. Return response
    return {
        "message": "AI plan and tasks generated successfully",
        "plan_id": new_plan.id,
        "goal_id": goal_id,
        "summary": new_plan.summary,
        "total_tasks_created": len(task_titles),
        "plan": new_plan.plan_data,
    }


@app.get("/goals/{goal_id}/plans")
def list_goal_plans(
    goal_id: int,
    db: DatabaseSession,
):
    goal = db.get(models.Goal, goal_id)

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    statement = (
        select(models.Plan)
        .where(models.Plan.goal_id == goal_id)
        .order_by(models.Plan.created_at.desc())
    )

    plans = db.scalars(statement).all()

    return plans