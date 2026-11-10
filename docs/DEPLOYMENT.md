# ModelForge — Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Python 3.12
- kubectl
- AWS CLI v2
- Terraform
- AWS credentials with appropriate permissions

## Local Development
1. Activate the virtual environment: `source .venv/bin/activate`
2. Install backend dependencies: `pip install -r backend/requirements.txt`
3. Start PostgreSQL using the configured local Docker container.
4. Configure database and API credentials using environment variables.
5. Apply migrations from the backend directory: `alembic upgrade head`
6. Start FastAPI from the backend directory: `uvicorn main:app --reload`
7. Start Streamlit: `streamlit run frontend/app.py`

## AWS Deployment Architecture
- Terraform provisions the VPC, EKS cluster, ECR repositories, and RDS PostgreSQL.
- Docker images are published to Amazon ECR.
- Kubernetes manifests deploy FastAPI and Streamlit.
- Amazon EBS CSI provides persistent model artifact storage.
- Kubernetes Secrets provide application credentials.

## Existing EKS Demonstration
Region: ap-south-1
Cluster: modelforge-demo
Namespace: modelforge

## Verify Kubernetes Workloads
```bash
kubectl -n modelforge get pods
kubectl -n modelforge get deployments
kubectl -n modelforge get svc
kubectl -n modelforge get pvc
```

## Access the Application
```bash
kubectl -n modelforge port-forward svc/modelforge-frontend 8501:8501
```
Open http://localhost:8501 in your browser.

Backend API documentation can be accessed through a separate port-forward:
```bash
kubectl -n modelforge port-forward svc/modelforge-backend 8000:8000
```
Open http://localhost:8000/docs.

## Security
Do not commit API keys, database passwords, AWS credentials, Terraform state, or Terraform plan files.

## Known Limitations
The managed EKS node group reported CREATE_FAILED despite a Ready worker. Private organization-wide access is planned but not yet implemented. EBS-backed model storage currently supports a single backend replica.

## Cleanup
After completing demonstrations and capturing evidence, destroy cloud infrastructure using the reviewed Terraform configuration and verify manually created resources are removed. Do not destroy infrastructure without explicit authorization.
