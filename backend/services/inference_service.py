import hashlib
from pathlib import Path

import joblib
import numpy as np

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.ml_model import MLModel

from core.config import ARTIFACT_DIR





def predict_model(
    model_id: int,
    features: list[float],
    db: Session,
):
    model_record = (
        db.query(MLModel)
        .filter(MLModel.id == model_id)
        .first()
    )

    if model_record is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found",
        )

    if not model_record.artifact_path:
        raise HTTPException(
            status_code=400,
            detail="No artifact uploaded for this model",
        )

    artifact_path = (
        ARTIFACT_DIR / model_record.artifact_path
    ).resolve()

    if not artifact_path.is_relative_to(
        ARTIFACT_DIR.resolve()
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact path",
        )

    if not artifact_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Model artifact file not found",
        )

    if not model_record.artifact_sha256:
        raise HTTPException(
            status_code=403,
            detail="Artifact checksum missing; re-upload required",
        )

    sha256 = hashlib.sha256()

    with artifact_path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            sha256.update(chunk)

    if sha256.hexdigest() != model_record.artifact_sha256:
        raise HTTPException(
            status_code=409,
            detail="Artifact integrity verification failed",
        )

    if (
        not model_record.approved_artifact_sha256
        or model_record.approved_artifact_sha256 != model_record.artifact_sha256
    ):
        raise HTTPException(
            status_code=403,
            detail="Model artifact is not approved for inference",
        )

    try:
        # Load only artifacts that pass integrity and approval checks.
        ml_model = joblib.load(artifact_path)

        input_data = np.array(
            [features],
            dtype=float,
        )

        prediction = ml_model.predict(input_data)

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid input features for this model",
        )

    return {
        "model_id": model_id,
        "model_name": model_record.name,
        "model_version": model_record.version,
        "prediction": prediction.tolist(),
    }