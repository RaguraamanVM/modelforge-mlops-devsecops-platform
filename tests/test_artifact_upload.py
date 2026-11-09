
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import main
from database import get_db
from models.ml_model import MLModel


@pytest.fixture
def upload_client(tmp_path, monkeypatch):
    # Redirect uploads to temporary storage.
    monkeypatch.setattr(main, "ARTIFACT_DIR", tmp_path)

    # Create an in-memory model (no PostgreSQL writes).
    model = MLModel(
        id=123,
        name="test-upload-model",
        version="1.0",
        status="registered",
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = model

    def override_get_db():
        yield db

    main.app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(main.app) as client:
            yield client, model, db, tmp_path
    finally:
        main.app.dependency_overrides.pop(get_db, None)


def test_successful_artifact_upload(upload_client):
    client, model, db, storage = upload_client

    content = b"dummy model artifact"

    response = client.post(
        "/models/123/artifact",
        files={
            "file": ("model.joblib", BytesIO(content),
                     "application/octet-stream")
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["model_id"] == 123
    assert data["size_bytes"] == len(content)
    assert data["filename"].endswith(".joblib")

    stored_file = storage / model.artifact_path
    assert stored_file.exists()
    assert stored_file.read_bytes() == content

    db.commit.assert_called_once()


def test_invalid_artifact_extension(upload_client):
    client, model, db, storage = upload_client

    response = client.post(
        "/models/123/artifact",
        files={"file": ("model.txt", b"invalid", "text/plain")},
    )

    assert response.status_code == 400
    assert not list(storage.rglob("*"))
    db.commit.assert_not_called()


def test_artifact_model_not_found(upload_client):
    client, model, db, storage = upload_client

    db.query.return_value.filter.return_value.first.return_value = None

    response = client.post(
        "/models/999/artifact",
        files={"file": ("model.joblib", b"data",
                        "application/octet-stream")},
    )

    assert response.status_code == 404
    db.commit.assert_not_called()


def test_oversized_artifact_upload(upload_client, monkeypatch):
    client, model, db, storage = upload_client

    # Lower the test limit to avoid allocating 50+ MiB.
    monkeypatch.setattr(main, "MAX_ARTIFACT_SIZE", 10)

    response = client.post(
        "/models/123/artifact",
        files={"file": ("model.joblib", b"x" * 11,
                        "application/octet-stream")},
    )

    assert response.status_code == 413
    assert not list(storage.rglob("*.joblib"))
    db.commit.assert_not_called()
