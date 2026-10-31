
import json

from app.planning import generate_plan


sample_goal = {
    "domain": "business",
    "title": "Increase monthly sales",
    "description": "Improve overall shop performance",
    "current_state": "Current monthly sales are 50000 rupees",
    "target_state": "Reach 100000 rupees in monthly sales",
    "timeline_value": 3,
    "timeline_unit": "months",
    "resources": "2 hours daily",
}


try:
    plan = generate_plan(sample_goal)

    print("\nAI GENERATED PLAN")
    print("=================")

    print(json.dumps(plan, indent=4))

except RuntimeError as error:
    print("Planning failed:", error)
