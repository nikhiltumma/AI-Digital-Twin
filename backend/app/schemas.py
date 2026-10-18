
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JournalEntryCreate(BaseModel):
    content: str = Field(min_length=1)


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_at: datetime


class JournalExtraction(BaseModel):
    purpose: str = Field(
        description="The user's stated purpose or goal"
    )
    actions: list[str] = Field(
        description="Actions explicitly mentioned"
    )
    deadline: str | None = Field(
        default=None,
        description="The stated deadline, or null if not mentioned",
    )
    blockers: list[str] = Field(
        description="Challenges or obstacles that may hinder progress"
    )

class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    target_date: datetime | None = None


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    target_date: datetime | None
    status: str
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    goal_id: int
    title: str
    completed: bool
    created_at: datetime


class ProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    goal_id: int
    completed_tasks: int
    total_tasks: int
    percentage: float
    calculated_at: datetime