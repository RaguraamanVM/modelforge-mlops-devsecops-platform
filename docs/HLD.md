# ModelForge — High-Level Design

## 1. Purpose
ModelForge is an internal MLOps platform for registering, managing, approving, and serving trained machine learning models.

## 2. System Components
- Streamlit: web interface for model management
- FastAPI: REST API and inference service
- PostgreSQL: model metadata and approval records
- Model artifact storage: local filesystem during development, Amazon EBS on EKS
- Docker: application containerization
- Kubernetes: workload orchestration

## 3. AWS Architecture
- Amazon VPC: cloud networking
- Amazon EKS: application workloads
- Amazon ECR: container image repositories
- Amazon RDS PostgreSQL: managed metadata database
- Amazon EBS CSI driver and PVC: persistent artifact storage
- Terraform: infrastructure provisioning

## 4. Request Flow
1. An ML engineer registers a model through Streamlit or FastAPI.
2. FastAPI saves model metadata in PostgreSQL.
3. The engineer uploads a serialized model artifact.
4. ModelForge stores the artifact and records its SHA-256 checksum.
5. An administrator approves the artifact.
6. An authorized client requests a prediction.
7. FastAPI loads the approved artifact and returns the prediction.

## 5. Security
- API-key authentication for protected operations
- Administrative approval controls
- Artifact integrity verification
- Kubernetes Secrets for runtime credentials
- Non-root application containers and restricted security contexts

## 6. Availability and Storage
- Kubernetes readiness and liveness probes
- Resource requests and limits
- PostgreSQL persistence through RDS
- Artifact persistence through an EBS-backed PVC
- Single-replica artifact storage; full high availability is not implemented

## 7. Network Access
Current Kubernetes Services use ClusterIP and are private to the cluster. Local port forwarding provides demonstration access. A shared internal URL using private connectivity, internal ALB, and private DNS is a future enhancement.

## 8. Known Infrastructure Issue
The EKS managed node group reported CREATE_FAILED despite a Ready worker node. The application was demonstrated successfully, but this issue remains unresolved.
