
import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


def generate_plan(goal: dict) -> dict:
    """
    Generate a personalized plan using the local Ollama model.
    """

    timeline_value = goal.get("timeline_value")
    timeline_unit = goal.get("timeline_unit")

    if not isinstance(timeline_value, int) or timeline_value <= 0:
        raise ValueError("A valid positive timeline is required")

    if timeline_unit != "months":
        raise ValueError("Currently, planning supports monthly timelines only")

    prompt = f"""
You are an intelligent planning assistant.

Create a practical personalized plan using these details:

Domain: {goal.get("domain")}
Goal: {goal.get("title")}
Description: {goal.get("description")}
Current situation: {goal.get("current_state")}
Expected outcome: {goal.get("target_state")}
Timeline: {timeline_value} months
Available resources: {goal.get("resources")}

STRICT PLANNING REQUIREMENTS:

1. Generate exactly {timeline_value} monthly milestones.
2. Every month MUST contain exactly FOUR weekly targets.
3. Every week MUST contain at least two actionable tasks.
4. Week numbers must be exactly 1, 2, 3, and 4 in each month.
5. Month numbers must be sequential starting from 1.
6. Tasks must be relevant to the milestone objective.
7. Respect the user's available resources and timeline.
8. Make the plan practical and achievable.
9. Do not skip any month or week.
10. Do not provide a shortened plan.

Return ONLY valid JSON using this structure:

{{
    "summary": "Short plan summary",
    "milestones": [
        {{
            "title": "Month 1: Milestone title",
            "month": 1,
            "objective": "Milestone objective",
            "weekly_targets": [
                {{
                    "week": 1,
                    "tasks": [
                        "First activity",
                        "Second activity"
                    ]
                }},
                {{
                    "week": 2,
                    "tasks": [
                        "First activity",
                        "Second activity"
                    ]
                }},
                {{
                    "week": 3,
                    "tasks": [
                        "First activity",
                        "Second activity"
                    ]
                }},
                {{
                    "week": 4,
                    "tasks": [
                        "First activity",
                        "Second activity"
                    ]
                }}
            ]
        }}
    ]
}}

Generate exactly {timeline_value} monthly milestones.
Each milestone must contain exactly four weekly targets.

Return JSON only. Do not use Markdown.
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 4096,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))

        if result.get("done_reason") == "length":
            raise ValueError("AI response was cut off due to output length")

        generated_text = result.get("response", "")
        plan = json.loads(generated_text)

        if not isinstance(plan, dict):
            raise ValueError("AI response must be a JSON object")

        if not isinstance(plan.get("summary"), str) or not plan["summary"].strip():
            raise ValueError("AI response is missing a valid summary")

        milestones = plan.get("milestones")

        if not isinstance(milestones, list):
            raise ValueError("AI response is missing milestones")

        # Validate the number of monthly milestones
        if len(milestones) != timeline_value:
            raise ValueError(
                f"Expected {timeline_value} milestones, "
                f"but received {len(milestones)}"
            )

        # Validate every month's weekly targets
        for month_index, milestone in enumerate(milestones, start=1):

            if not isinstance(milestone, dict):
                raise ValueError("Invalid milestone structure")

            if milestone.get("month") != month_index:
                raise ValueError(
                    f"Expected month number {month_index}"
                )

            weekly_targets = milestone.get("weekly_targets")

            if not isinstance(weekly_targets, list):
                raise ValueError(
                    f"Month {month_index} is missing weekly targets"
                )

            if len(weekly_targets) != 4:
                raise ValueError(
                    f"Month {month_index} must contain exactly four weeks"
                )

            for week_index, week_data in enumerate(weekly_targets, start=1):

                if not isinstance(week_data, dict):
                    raise ValueError("Invalid weekly target structure")

                if week_data.get("week") != week_index:
                    raise ValueError(
                        f"Month {month_index} has incorrect week numbering"
                    )

                tasks = week_data.get("tasks")

                if not isinstance(tasks, list) or len(tasks) < 2:
                    raise ValueError(
                        f"Month {month_index}, Week {week_index} "
                        "must contain at least two tasks"
                    )

                if not all(
                    isinstance(task, str) and task.strip()
                    for task in tasks
                ):
                    raise ValueError("Invalid task in generated plan")

        return plan

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Unable to connect to Ollama. Make sure Ollama is running."
        ) from exc

    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"Invalid AI plan: {exc}"
        ) from exc
