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

    try:
        # Only load trusted model artifacts.
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