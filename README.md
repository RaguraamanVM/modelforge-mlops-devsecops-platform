# ModelForge

A containerized MLOps platform for registering, versioning, approving, and serving machine learning models.

## Technology Stack

- Backend: Python 3.12, FastAPI
- Frontend: Streamlit
- Database: PostgreSQL, SQLAlchemy, Alembic
- ML: scikit-learn, joblib
- Containers: Docker
- Cloud: AWS EKS, ECR, RDS, EBS
- Infrastructure: Terraform, Kubernetes
- CI and Security: GitHub Actions, pytest, Trivy

## Features

- Model registration and versioning
- Model artifact upload and SHA-256 verification
- Administrative model approval
- Authenticated prediction API
- Streamlit web interface
- PostgreSQL metadata storage
- Persistent model storage on Amazon EBS
- Kubernetes health probes and resource limits
- Non-root container execution

## Architecture

See [Architecture](docs/ARCHITECTURE.md).

## Local Testing

    source .venv/bin/activate
    python -m pytest tests/ -q

Last verified: 30 tests passed.

## AWS Deployment

Region: ap-south-1

EKS cluster: modelforge-demo

Kubernetes namespace: modelforge

Infrastructure definitions: infrastructure/

## Project Status

Core model lifecycle and AWS inference have been demonstrated.

Known limitations include single-replica EBS artifact storage and an EKS managed node group requiring investigation.

## Security

ModelForge uses API keys, administrative approval, model checksums, and Kubernetes container security contexts.

Only upload trusted model artifacts. Loading untrusted pickle or joblib files can execute arbitrary code.

## Evidence

See docs/evidence/ for deployment evidence.
