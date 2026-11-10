# ModelForge — Low-Level Design

## 1. Backend Structure
- backend/main.py: FastAPI endpoints
- backend/database.py: SQLAlchemy database connectivity
- backend/models/ml_model.py: PostgreSQL ORM model
- backend/schemas/ml_model.py: Pydantic request and response schemas
- backend/services/inference_service.py: model inference logic
- backend/core/security.py: authentication and authorization helpers
- backend/core/config.py: artifact storage configuration
- backend/alembic/: database schema migrations

## 2. REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Application health |
| GET | /health/db | Database connectivity |
| POST | /models | Register model |
| GET | /models | List models |
| GET | /models/{model_id} | Retrieve model |
| PATCH | /models/{model_id} | Update metadata |
| DELETE | /models/{model_id} | Delete model record |
| POST | /models/{model_id}/artifact | Upload artifact |
| POST | /models/{model_id}/approve | Approve artifact |
| POST | /models/{model_id}/predict | Run inference |

## 3. PostgreSQL Schema
Table: ml_models

| Column | Type | Purpose |
|---|---|---|
| id | Integer | Primary key |
| name | String(100) | Model name |
| version | String(50) | Model version |
| description | Text | Optional description |
| framework | String(50) | ML framework |
| status | String(30) | Lifecycle status |
| artifact_path | String(500) | Artifact location |
| artifact_filename | String(255) | Original filename |
| artifact_size_bytes | BigInteger | Artifact size |
| artifact_sha256 | String(64) | Artifact checksum |
| approved_artifact_sha256 | String(64) | Approved checksum |
| artifact_approved_at | Timestamp | Approval timestamp |
| created_at | Timestamp | Creation timestamp |

## 4. Artifact Storage
Local development stores model artifacts in a configurable filesystem directory. AWS EKS uses an EBS-backed Kubernetes PersistentVolumeClaim mounted into the backend container.

## 5. Inference Flow
1. Receive a prediction request containing a list of numeric features.
2. Validate request data using Pydantic.
3. Retrieve model metadata from PostgreSQL.
4. Verify artifact availability and approval requirements.
5. Load the serialized model artifact.
6. Execute inference and return predictions.

## 6. Kubernetes
- Backend Deployment and ClusterIP Service
- Frontend Deployment and ClusterIP Service
- EBS CSI driver, StorageClass, and PersistentVolumeClaim
- Readiness and liveness probes
- CPU and memory resource constraints
- Non-root container security contexts

## 7. Testing
Automated tests cover API behavior, artifact upload, approval, and inference. Last verified local test run: 30 passed.

## 8. Limitations
Model artifacts must be trusted because joblib and pickle deserialization can execute code. EBS ReadWriteOnce storage is not designed for unrestricted multi-node sharing. Production HA and organization-wide private access are not yet implemented.
