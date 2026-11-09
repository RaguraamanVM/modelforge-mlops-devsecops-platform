import os
from pathlib import Path

DEFAULT_ARTIFACT_DIR = (
    Path(__file__).resolve().parents[2]
    / "storage"
    / "models"
)

ARTIFACT_DIR = Path(
    os.getenv("MODEL_ARTIFACT_DIR", str(DEFAULT_ARTIFACT_DIR))
).resolve()