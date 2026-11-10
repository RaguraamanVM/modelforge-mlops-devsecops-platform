import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import main


@pytest.fixture
def approval_client(monkeypatch):
    monkeypatch.setenv("MODELFORGE_API_KEY", "test-regular-key")
    monkeypatch.setenv("MODELFORGE_ADMIN_KEY", "test-admin-key")

    with TestClient(main.app) as client:
        yield client


def test_approval_without_admin_key(approval_client):
    response = approval_client.post(
        "/models/123/approve",
        json={"expected_sha256": "a" * 64},
    )

    assert response.status_code == 401


def test_approval_with_invalid_admin_key(approval_client):
    response = approval_client.post(
        "/models/123/approve",
        headers={"X-Admin-Key": "incorrect-key"},
        json={"expected_sha256": "a" * 64},
    )

    assert response.status_code == 401


def test_approval_rejects_regular_api_key(approval_client):
    response = approval_client.post(
        "/models/123/approve",
        headers={"X-Admin-Key": "test-regular-key"},
        json={"expected_sha256": "a" * 64},
    )

    assert response.status_code == 401


def test_approval_rejects_malformed_checksum(approval_client):
    response = approval_client.post(
        "/models/123/approve",
        headers={"X-Admin-Key": "test-admin-key"},
        json={"expected_sha256": "invalid"},
    )

    assert response.status_code == 422


def test_successful_artifact_approval(approval_client, tmp_path, monkeypatch):
    import hashlib
    from unittest.mock import MagicMock
    from database import get_db
    from models.ml_model import MLModel

    monkeypatch.setattr(main, "ARTIFACT_DIR", tmp_path)

    artifact = tmp_path / "123" / "model.joblib"
    artifact.parent.mkdir()
    artifact.write_bytes(b"trusted-test-artifact")
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()

    model = MLModel(
        id=123,
        name="approval-test",
        version="1.0",
        artifact_path="123/model.joblib",
        artifact_sha256=checksum,
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = model
    main.app.dependency_overrides[get_db] = lambda: db

    try:
        response = approval_client.post(
            "/models/123/approve",
            headers={"X-Admin-Key": "test-admin-key"},
            json={"expected_sha256": checksum},
        )

        assert response.status_code == 200
        assert model.approved_artifact_sha256 == checksum
        assert model.artifact_approved_at is not None
        db.commit.assert_called_once()
    finally:
        main.app.dependency_overrides.pop(get_db, None)


def test_approval_rejects_checksum_mismatch(
    approval_client, tmp_path, monkeypatch
):
    from unittest.mock import MagicMock
    from database import get_db
    from models.ml_model import MLModel

    monkeypatch.setattr(main, "ARTIFACT_DIR", tmp_path)

    model = MLModel(
        id=123,
        name="approval-test",
        version="1.0",
        artifact_path="123/model.joblib",
        artifact_sha256="a" * 64,
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = model
    main.app.dependency_overrides[get_db] = lambda: db

    try:
        response = approval_client.post(
            "/models/123/approve",
            headers={"X-Admin-Key": "test-admin-key"},
            json={"expected_sha256": "b" * 64},
        )

        assert response.status_code == 409
        assert model.approved_artifact_sha256 is None
        db.commit.assert_not_called()
    finally:
        main.app.dependency_overrides.pop(get_db, None)


def test_approval_rejects_tampered_artifact(
    approval_client, tmp_path, monkeypatch
):
    import hashlib
    from unittest.mock import MagicMock
    from database import get_db
    from models.ml_model import MLModel

    monkeypatch.setattr(main, "ARTIFACT_DIR", tmp_path)

    original = b"original-model-artifact"
    checksum = hashlib.sha256(original).hexdigest()

    artifact = tmp_path / "123" / "model.joblib"
    artifact.parent.mkdir()
    artifact.write_bytes(b"tampered-model-artifact")

    model = MLModel(
        id=123,
        name="approval-test",
        version="1.0",
        artifact_path="123/model.joblib",
        artifact_sha256=checksum,
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = model
    main.app.dependency_overrides[get_db] = lambda: db

    try:
        response = approval_client.post(
            "/models/123/approve",
            headers={"X-Admin-Key": "test-admin-key"},
            json={"expected_sha256": checksum},
        )

        assert response.status_code == 409
        assert model.approved_artifact_sha256 is None
        assert model.artifact_approved_at is None
        db.commit.assert_not_called()
    finally:
        main.app.dependency_overrides.pop(get_db, None)
