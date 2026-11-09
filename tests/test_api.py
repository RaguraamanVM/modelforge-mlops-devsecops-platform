import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app

client = TestClient(app)


def test_openapi_schema():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/models/{model_id}/predict" in response.json()["paths"]


def test_prediction_validation():
    response = client.post(
        "/models/2/predict",
        json={"features": []},
    )

    assert response.status_code == 422


def test_prediction_missing_features():
    response = client.post(
        "/models/2/predict",
        json={},
    )

    assert response.status_code == 422