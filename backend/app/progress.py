
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


def calculate_goal_progress(db: Session, goal_id: int) -> dict:
    statement = select(models.Task).where(
        models.Task.goal_id == goal_id
    )

    tasks = db.scalars(statement).all()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.completed)

    percentage = (
        round((completed_tasks / total_tasks) * 100, 2)
        if total_tasks > 0
        else 0.0
    )

    return {
        "goal_id": goal_id,
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "percentage": percentage,
    }
