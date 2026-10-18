
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
