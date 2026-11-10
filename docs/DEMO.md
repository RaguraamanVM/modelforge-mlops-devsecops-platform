# ModelForge — Demonstration Guide

## 1. Demonstration Objective
Demonstrate an MLOps platform running on AWS EKS with model registration, artifact management, PostgreSQL persistence, and machine learning inference.

## 2. Demonstration Sequence (5–7 Minutes)

### 0:00–0:45 — Introduction
Explain the problem: ML teams need a consistent way to register, track, and serve trained models.

### 0:45–1:45 — AWS Architecture
Show the architecture:
- Streamlit frontend
- FastAPI backend
- Amazon EKS
- Amazon RDS PostgreSQL
- Amazon EBS persistent storage
- Amazon ECR
- Terraform infrastructure

### 1:45–3:15 — Model Registry
Show the Streamlit interface and registered iris-classifier model.
Explain metadata, model versions, and artifact checksum tracking.
Mention the administrative approval endpoint without claiming the approval workflow was demonstrated.

### 3:15–4:30 — Live Inference
Use the authenticated prediction API.

Endpoint:
POST /models/1/predict

Example request:
{"features": [5.1, 3.5, 1.4, 0.2]}

Previously verified response:
{"model_id": 1, "model_name": "iris-classifier", "model_version": "v1.0", "prediction": [0]}

Explain that the trained model performs inference using supplied features.

### 4:30–5:30 — Kubernetes Evidence
Show:
- Backend and frontend Deployments
- Running Pods
- ClusterIP Services
- PersistentVolumeClaim
- Application health endpoints

### 5:30–6:30 — DevOps Practices
Explain:
- Docker containerization
- Terraform infrastructure as code
- Kubernetes workload deployment
- Database migrations using Alembic
- Automated pytest tests
- GitHub Actions CI configuration
- Container vulnerability scanning configuration

Do not claim successful remote CI execution unless verified.

### 6:30–7:00 — Limitations and Improvements
Discuss:
- EKS managed node group CREATE_FAILED status
- Single-replica backend storage
- No shared internal application URL yet
- Production hardening and high availability as future work

## 3. Recording Safety
- Never show AWS credentials, API keys, passwords, or Kubernetes Secret values.
- Avoid exposing private environment files.
- Record only after confirming the application is accessible.
- Keep the demonstration focused on verified functionality.

## 4. Interview Summary
ModelForge demonstrates practical integration of Python APIs, PostgreSQL, Docker, Kubernetes, AWS infrastructure, persistent storage, testing, and infrastructure as code.

It is a portfolio demonstration, not a production-ready managed MLOps service.
