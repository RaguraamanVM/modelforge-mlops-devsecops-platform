# ModelForge Architecture

## Components
- Streamlit: web interface
- FastAPI: model registry and inference API
- PostgreSQL: model metadata
- Amazon EBS: persistent model artifacts

## AWS Infrastructure
- Amazon EKS: Kubernetes workloads
- Amazon ECR: container images
- Amazon RDS: PostgreSQL database
- Terraform: infrastructure as code

## Model Lifecycle
Register -> Upload -> Verify SHA-256 -> Approve -> Predict

## Security
API keys, non-root containers, Kubernetes Secrets, disabled privilege escalation, dropped capabilities, and seccomp.

## Reliability
Health probes, resource limits, persistent storage, and database migrations.

## Known Limitations
EBS ReadWriteOnce storage, unresolved EKS node-group CREATE_FAILED status, and no full high-availability configuration.
