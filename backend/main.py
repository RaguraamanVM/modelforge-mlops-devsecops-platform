from core.security import require_api_key
from core.config import ARTIFACT_DIR
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from models.ml_model import MLModel
from schemas.ml_model import MLModelCreate, MLModelUpdate, MLModelResponse

from database import engine


from pathlib import Path
from uuid import uuid4
from fastapi import File, UploadFile

from fastapi import HTTPException
from schemas.ml_model import PredictionRequest

from services.inference_service import predict_model as run_inference

from core.config import ARTIFACT_DIR

app = FastAPI(
    title="ModelForge API",
    description="A lightweight MLOps model registry and inference platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "ModelForge",
        "version": "0.1.0",
    }


@app.get("/health/db")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "postgresql",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

@app.post("/models", response_model=MLModelResponse, status_code=201)
def register_model(
    model_data: MLModelCreate,
    db: Session = Depends(get_db)
):
    existing_model = (
        db.query(MLModel)
        .filter(
            MLModel.name == model_data.name,
            MLModel.version == model_data.version
        )
        .first()
    )

    if existing_model:
        raise HTTPException(
            status_code=409,
            detail="Model with this name and version already exists"
        )

    new_model = MLModel(
        name=model_data.name,
        version=model_data.version,
        description=model_data.description,
        framework=model_data.framework
    )

    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    return new_model

@app.get("/models", response_model=list[MLModelResponse])
def get_models(db: Session = Depends(get_db)):
    models = db.query(MLModel).all()
    return models



@app.get("/models/{model_id}", response_model=MLModelResponse)
def get_model_by_id(
    model_id: int,
    db: Session = Depends(get_db)
):
    model = db.query(MLModel).filter(
        MLModel.id == model_id
    ).first()

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found"
        )

    return model


@app.delete("/models/{model_id}", status_code=204)
def delete_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    model = db.query(MLModel).filter(
        MLModel.id == model_id
    ).first()

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found"
        )

    db.delete(model)
    db.commit()


@app.patch("/models/{model_id}", response_model=MLModelResponse)
def update_model(
    model_id: int,
    model_data: MLModelUpdate,
    db: Session = Depends(get_db)
):
    model = db.query(MLModel).filter(
        MLModel.id == model_id
    ).first()

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found"
        )

    updates = model_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(model, field, value)

    db.commit()
    db.refresh(model)

    return model



MAX_ARTIFACT_SIZE = 50 * 1024 * 1024

@app.post("/models/{model_id}/artifact", status_code=201)
async def upload_model_artifact(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
):
    model = db.query(MLModel).filter(
        MLModel.id == model_id
    ).first()

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found"
        )

    filename = file.filename or ""

    if Path(filename).suffix.lower() not in {".pkl", ".joblib"}:
        raise HTTPException(
            status_code=400,
            detail="Only .pkl and .joblib files are supported"
        )

    model_dir = ARTIFACT_DIR / str(model_id)
    model_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{Path(filename).suffix.lower()}"
    artifact_path = model_dir / stored_filename
    total_size = 0

    try:
        with artifact_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > MAX_ARTIFACT_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Artifact exceeds the 50 MB limit"
                    )

                output.write(chunk)

    except Exception:
        artifact_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()

    # Save artifact metadata in PostgreSQL
    model.artifact_path = f"{model_id}/{stored_filename}"
    model.artifact_filename = stored_filename
    model.artifact_size_bytes = total_size

    try:
        db.commit()
        db.refresh(model)
    except Exception:
        db.rollback()
        artifact_path.unlink(missing_ok=True)
        raise

    return {
        "message": "Model artifact uploaded successfully",
        "model_id": model_id,
        "filename": stored_filename,
        "size_bytes": total_size
    }


@app.post("/models/{model_id}/predict")
def predict_model(
    model_id: int,
    request: PredictionRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
):
    return run_inference(
        model_id=model_id,
        features=request.features,
        db=db,
    )