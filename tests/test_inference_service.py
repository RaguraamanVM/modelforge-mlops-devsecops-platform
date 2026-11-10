import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi import HTTPException

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from services.inference_service import predict_model


def mock_db_record(record):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = record
    return db


def test_model_not_found():
    db = mock_db_record(None)

    with pytest.raises(HTTPException) as exc:
        predict_model(999, [5.1, 3.5, 1.4, 0.2], db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Model not found"


def test_model_without_artifact():
    record = SimpleNamespace(artifact_path=None)
    db = mock_db_record(record)

    with pytest.raises(HTTPException) as exc:
        predict_model(2, [5.1, 3.5, 1.4, 0.2], db)

    assert exc.value.status_code == 400


def test_successful_prediction(tmp_path, monkeypatch):
    from services import inference_service

    monkeypatch.setattr(inference_service, "ARTIFACT_DIR", tmp_path)
    artifact = tmp_path / "2" / "model.joblib"
    artifact.parent.mkdir()
    artifact.write_bytes(b"trusted-test-artifact")
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()

    record = SimpleNamespace(
        name="iris-classifier",
        version="1.0",
        artifact_path="2/model.joblib",
        artifact_sha256=checksum,
    )
    db = mock_db_record(record)

    fake_model = MagicMock()
    fake_model.predict.return_value = np.array([0])

    with (
        patch(
            "services.inference_service.joblib.load",
            return_value=fake_model,
        ),
    ):
        result = predict_model(
            2,
            [5.1, 3.5, 1.4, 0.2],
            db,
        )

    assert result["prediction"] == [0]
    assert result["model_name"] == "iris-classifier"
    assert result["model_version"] == "1.0"

    fake_model.predict.assert_called_once()


def test_invalid_prediction_features(tmp_path, monkeypatch):
    from services import inference_service

    monkeypatch.setattr(inference_service, "ARTIFACT_DIR", tmp_path)
    artifact = tmp_path / "2" / "model.joblib"
    artifact.parent.mkdir()
    artifact.write_bytes(b"trusted-test-artifact")
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()

    record = SimpleNamespace(
        name="iris-classifier",
        version="1.0",
        artifact_path="2/model.joblib",
        artifact_sha256=checksum,
    )
    db = mock_db_record(record)

    fake_model = MagicMock()
    fake_model.predict.side_effect = ValueError(
        "Incorrect number of features"
    )

    with (
        patch(
            "services.inference_service.joblib.load",
            return_value=fake_model,
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            predict_model(2, [1.0, 2.0], db)

    assert exc.value.status_code == 422
    assert exc.value.detail == (
        "Invalid input features for this model"
    )


def test_artifact_path_traversal_blocked():
    record = SimpleNamespace(
        name="unsafe-model",
        version="1.0",
        artifact_path="../../../../etc/passwd",
    )
    db = mock_db_record(record)

    with pytest.raises(HTTPException) as exc:
        predict_model(2, [5.1, 3.5, 1.4, 0.2], db)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid artifact path"


def test_missing_artifact_file():
    record = SimpleNamespace(
        name="iris-classifier",
        version="1.0",
        artifact_path="2/missing.joblib",
    )
    db = mock_db_record(record)

    with patch(
        "services.inference_service.Path.is_file",
        return_value=False,
    ):
        with pytest.raises(HTTPException) as exc:
            predict_model(2, [5.1, 3.5, 1.4, 0.2], db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Model artifact file not found"


def test_missing_artifact_checksum(tmp_path, monkeypatch):
    from services import inference_service

    monkeypatch.setattr(inference_service, "ARTIFACT_DIR", tmp_path)
    artifact = tmp_path / "2" / "model.joblib"
    artifact.parent.mkdir()
    artifact.write_bytes(b"test-artifact")

    record = SimpleNamespace(
        artifact_path="2/model.joblib",
        artifact_sha256=None,
    )

    with pytest.raises(HTTPException) as exc:
        predict_model(2, [1.0], mock_db_record(record))

    assert exc.value.status_code == 403


def test_artifact_checksum_mismatch(tmp_path, monkeypatch):
    from services import inference_service

    monkeypatch.setattr(inference_service, "ARTIFACT_DIR", tmp_path)
    artifact = tmp_path / "2" / "model.joblib"
    artifact.parent.mkdir()
    artifact.write_bytes(b"modified-artifact")

    record = SimpleNamespace(
        artifact_path="2/model.joblib",
        artifact_sha256="0" * 64,
    )

    with patch("services.inference_service.joblib.load") as loader:
        with pytest.raises(HTTPException) as exc:
            predict_model(2, [1.0], mock_db_record(record))

        loader.assert_not_called()

    assert exc.value.status_code == 409
