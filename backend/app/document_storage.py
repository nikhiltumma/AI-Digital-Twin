from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Directory for uploaded goal documents
DOCUMENT_STORAGE_DIR = (
    PROJECT_ROOT / "backend" / "storage" / "goal_documents"
)

# Create directory if it doesn't exist
DOCUMENT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Upload restrictions
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".txt",
}