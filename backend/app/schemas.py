
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    domain: str = Field(default="general", max_length=50)
    description: str | None = None
    current_state: str | None = None
    target_state: str | None = None
    timeline_value: int | None = Field(default=None, gt=0)
    timeline_unit: str | None = None
    resources: str | None = None
    target_date: datetime | None = None

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        allowed_domains = {
            "general",
            "education",
            "healthcare",
            "business",
            "agriculture",
            "transport",
            "manufacturing",
        }

        value = value.strip().lower()

        if value not in allowed_domains:
            raise ValueError(
                f"Domain must be one of: {', '.join(sorted(allowed_domains))}"
            )

        return value

    @field_validator("timeline_unit")
    @classmethod
    def validate_timeline_unit(cls, value: str | None) -> str | None:
        if value is None:
            return value

        allowed_units = {"days", "weeks", "months", "years"}
        value = value.strip().lower()

        if value not in allowed_units:
            raise ValueError(
                f"Timeline unit must be one of: {', '.join(sorted(allowed_units))}"
            )

        return value


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    domain: str
    description: str | None
    current_state: str | None
    target_state: str | None
    timeline_value: int | None
    timeline_unit: str | None
    resources: str | None
    target_date: datetime | None
    status: str
    created_at: datetime

class GoalDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    goal_id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: datetime

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