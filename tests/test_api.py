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


def test_prediction_validation(monkeypatch):
    monkeypatch.setenv("MODELFORGE_API_KEY", "test-only-api-key")
    response = client.post(
        "/models/2/predict",
        headers={"X-API-Key": "test-only-api-key"},
        json={"features": []},
    )

    assert response.status_code == 422


def test_prediction_missing_features(monkeypatch):
    monkeypatch.setenv("MODELFORGE_API_KEY", "test-only-api-key")
    response = client.post(
        "/models/2/predict",
        headers={"X-API-Key": "test-only-api-key"},
        json={},
    )

    assert response.status_code == 422

def test_prediction_without_api_key(monkeypatch):
    monkeypatch.setenv("MODELFORGE_API_KEY", "test-only-api-key")

    response = client.post(
        "/models/2/predict",
        json={"features": [5.1, 3.5, 1.4, 0.2]},
    )

    assert response.status_code == 401


def test_prediction_with_invalid_api_key(monkeypatch):
    monkeypatch.setenv("MODELFORGE_API_KEY", "test-only-api-key")

    response = client.post(
        "/models/2/predict",
        headers={"X-API-Key": "incorrect-key"},
        json={"features": [5.1, 3.5, 1.4, 0.2]},
    )

    assert response.status_code == 401


def test_model_management_requires_api_key(monkeypatch):
    monkeypatch.setenv("MODELFORGE_API_KEY", "test-only-api-key")

    requests = [
        ("post", "/models", {"name": "test", "version": "1.0"}),
        ("patch", "/models/2", {"description": "unauthorized"}),
        ("delete", "/models/2", None),
    ]

    for method, url, payload in requests:
        response = client.request(
            method.upper(),
            url,
            json=payload,
        )
        assert response.status_code == 401, (
            f"{method.upper()} {url}: expected 401, got {response.status_code}"
        )
