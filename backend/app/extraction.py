
import json
import urllib.error
import urllib.request

from .schemas import JournalExtraction


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"


def extract_journal(content: str) -> JournalExtraction:
    prompt = f"""
You extract structured information from a personal journal.

Extract only information supported by the journal text.
- purpose: the user's stated goal or purpose.
- actions: specific actions the user plans to take or has stated.
- deadline: the stated deadline, or null if none is mentioned.
- blockers: challenges or obstacles that may hinder progress.
  Include explicitly stated difficulties, such as finding a topic difficult.

Do not invent information. Return only the requested JSON object.

Journal entry:
{content}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": JournalExtraction.model_json_schema(),
        "options": {"temperature": 0},
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned an invalid API response.") from exc

    response_text = result.get("response", "")

    try:
        extracted_data = json.loads(response_text)
        return JournalExtraction.model_validate(extracted_data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            "The AI response could not be parsed or validated."
        ) from exc
    