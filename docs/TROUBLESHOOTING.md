# ModelForge — Troubleshooting and Incident History

Project: ModelForge — ML Model Registry & Inference Platform
Environment: Windows 11, WSL2 Ubuntu 24.04, Python 3.12,
Docker Compose, FastAPI, PostgreSQL 17, Alembic, Streamlit

## Documentation Standards

Each record captures symptoms, investigation, cause,
resolution, verification, and engineering lessons.

Evidence classifications:
- CONFIRMED: Supported by observed commands or output.
- PARTIAL: Some details or final resolution need verification.
- OBSERVATION: Setup/testing event, not necessarily a defect.

Historical entries are reconstructed from project conversations.
Dates and commands are included only where supported.

---

## INC-001 — Docker Socket Permission Denied

Date: 2026-11-07
Status: PARTIAL — workaround confirmed

Symptoms:
Running `docker ps` or `docker info` without sudo produced
permission denied errors for /var/run/docker.sock.

Investigation:
- Docker client and Compose were installed.
- The raguuu account belonged to the docker group.
- The Docker socket was owned by root:root.
- Docker was running through Snap.
- Standard systemd Docker units were unavailable.

Root cause:
Docker socket ownership and permissions did not grant
the docker group access as expected.

Workaround:
Used sudo for Docker commands where necessary.

Verification:
`sudo docker ps` worked.

Lessons:
- Group membership alone does not guarantee socket access.
- Inspect socket ownership and daemon installation method.
- Avoid insecure blanket permission changes.
- Permanent resolution remains unverified.

---

## INC-002 — PostgreSQL Host Port 5432 Conflict

Date: 2026-11-07
Status: CONFIRMED

Symptoms:
Docker PostgreSQL could not use the intended host port 5432.

Investigation:
A native Ubuntu PostgreSQL process was already occupying
port 5432 (observed PID 419).

Root cause:
Two PostgreSQL instances attempted to use the same host port.

Resolution:
Changed Docker Compose port mapping to:

    127.0.0.1:5433:5432

The container continued listening on port 5432 internally.

Verification:
PostgreSQL 17 container became healthy.

Lessons:
- Host and container ports are separate namespaces.
- Local applications use the published host port.
- Containers on the Compose network use the service name
  and internal port.
- Bind local development databases to loopback when
  external exposure is unnecessary.

---

## INC-003 — Alembic Configuration Location Error

Date: 2026-11-07
Status: CONFIRMED

Symptoms:
Running Alembic from the backend/alembic directory produced:

    No 'script_location' key found

Root cause:
The command was executed from a directory where the expected
Alembic configuration was not being loaded.

Resolution:
Ran Alembic from the backend project directory.

Verification:
`alembic check` proceeded to detect model/schema changes,
including ml_models and indexes.

Lessons:
- Alembic commands depend on configuration discovery.
- Run migration commands from the documented directory,
  or supply an explicit configuration path.
- A successful configuration load does not automatically
  mean a migration has been applied.

---

## INC-004 — FastAPI Backend Port 8000 Already Occupied

Date: 2026-11-09
Status: CONFIRMED

Symptoms:
The Dockerized backend could not bind host port 8000.

Investigation:
A local Uvicorn/Python process was already using the port.

Root cause:
The local development server conflicted with the
containerized FastAPI service.

Resolution:
Stopped the conflicting local Uvicorn process and
recreated the backend service.

Verification:
GET /health returned the expected healthy response.
Database connectivity was separately checked with SELECT 1.

Lessons:
- Check for port conflicts before starting containers.
- Avoid running local and containerized servers on the same
  published port.
- A health endpoint confirms application availability,
  not necessarily every dependency.

---

## INC-005 — Model Artifact Storage and Permissions

Date: 2026-11-09
Status: CONFIRMED — final storage verification

Context:
The containerized backend runs as a non-root application user.

Investigation:
Verified the local storage bind mount:

    storage/models -> /storage/models

Confirmed application user UID 10001 could write to storage.

Resolution:
Configured persistent artifact storage with permissions
compatible with the non-root backend process.

Verification:
Artifact persistence survived backend container recreation.

Lessons:
- Container filesystem contents may disappear on recreation.
- Persistent storage must be mounted explicitly.
- Non-root container users require appropriate write access.
- Storage persistence and secure permissions should be
  verified independently.

Note:
Earlier individual permission-error text is not fully
reconstructed and should not be invented.

---

## INC-006 — Model Registration Returned HTTP 500

Date: 2026-11-10 (India local time)
Status: CONFIRMED — resolved

Symptoms:
Streamlit displayed "Model registration failed".
POST /models returned HTTP 500 Internal Server Error.

Investigation:
Ran:

    docker compose logs --tail=80 backend

The traceback identified backend/main.py, line 90:

    NameError: name 'new_mode' is not defined

Root cause:
The registration function returned an undefined variable:

    return new_mode

The intended variable was:

    return new_model

Database investigation:
GET /models confirmed customer-churn-demo, version 1.0,
had already been saved as model ID 4.

Resolution:
Corrected the return statement in backend/main.py.
Rebuilt the backend:

    docker compose up -d --build backend

Verification:
- GET /health returned HTTP 200.
- Existing models remained available.
- A new model, sentiment-analysis-demo, registered
  successfully through Streamlit.
- After dashboard refresh, model count increased from 2 to 3.

Lessons:
- HTTP 500 does not prove a database insert failed.
- Verify persisted state before retrying writes.
- Add regression tests for successful API responses.
- Consider duplicate protection and idempotency.
- Rebuild container images after source changes when needed.

---

## Additional Setup and Testing Observations

### Python virtual environment
Python 3.12 required suitable virtual-environment tooling.
The project ultimately used .venv successfully.
Exact initial error output and installation commands
require verification before being recorded as an incident.

### Docker Compose service configuration
On 2026-11-09, Compose initially listed only postgres.
The backend service was added with its database environment,
port configuration, and health dependency.

### Streamlit initial startup
The first Streamlit launch involved an onboarding prompt.
An interrupted run was followed by a successful launch.
The dashboard subsequently displayed backend health,
registered models, and the registration form.

### Automated testing
Nine pytest tests passed during the backend MVP phase.
A deprecation warning was observed.
The exact warning source and corrective action remain
to be documented.

### Git and repository hygiene
The initial backend MVP was committed to Git.
The repository used .gitignore rules for local environments,
secrets, and generated artifacts.
This is a security/development practice, not an incident.

---

## Follow-up Improvements

- Add a regression test for POST /models success responses.
- Check database state before retrying failed writes.
- Add duplicate-registration protection where appropriate.
- Verify the permanent Docker socket permission solution.
- Preserve exact error logs for future incidents.
- Keep architecture decisions in a separate document.
- Update this history whenever new issues are resolved.

---

# Phase 2 — AWS Deployment and Platform Engineering

## INC-007 — WSL2 Memory Pressure and Terminal Instability

**Status:** Mitigated

**Symptoms:** WSL2 experienced resource pressure and unstable terminal behavior during development and AWS deployment work.

**Action taken:** Configured Windows `.wslconfig` with 4 GB memory, 2 processors, and 4 GB swap.

**Verification:** WSL subsequently reported approximately 3.8 GiB RAM and 4 GiB swap, and the terminal was usable.

**Lesson:** Local workstation capacity must be considered when running Docker, Kubernetes tooling, and cloud deployment workflows.

## INC-008 — FastAPI NameError During Backend Development

**Status:** Resolved during development

**Symptoms:** A backend execution path raised a `NameError` involving `new_mode`.

**Resolution:** The application code was corrected during backend development. The exact patch and traceback are not preserved in this document.

**Lesson:** Run regression tests after modifying request handlers and database operations.

## INC-009 — EKS Managed Node Group Creation Failure

**Status:** Open — nonblocking for the current demonstration

**Symptoms:** The EKS managed node group reported `CREATE_FAILED` and `NodeCreationFailure`.

**Observed state:** At least one Kubernetes worker node became Ready, and the backend and frontend workloads ran successfully.

**Investigation:** Terraform and EKS recovery attempts were performed. A complete root cause has not been established.

**Decision:** Defer further node-group recovery to prioritize a working portfolio demonstration.

**Impact:** The deployment cannot be described as fully healthy or production-ready.

## INC-010 — Amazon EBS Persistent Storage Integration

**Status:** Operational with hardening limitations

**Context:** Model artifacts needed persistent storage beyond the backend container filesystem.

**Implementation:** Integrated Kubernetes persistent storage using Amazon EBS and the EBS CSI driver.

**Observed challenge:** The non-root backend process required write access to the mounted artifact directory.

**Current limitation:** The artifact directory was made writable using permissive filesystem permissions. This is not an acceptable final production security configuration.

**Follow-up:** Implement secure volume ownership and permissions, then retest artifact upload and inference.

## INC-011 — Kubernetes Service Access

**Status:** Resolved for local demonstration

**Symptoms:** Backend and frontend Services had no external IP address.

**Cause:** Both Services use Kubernetes `ClusterIP`, which does not provide a public endpoint.

**Workaround:** Use `kubectl port-forward` to access the Streamlit frontend and FastAPI backend from the local workstation.

**Limitation:** Organization-wide access through private networking, an internal ALB, private DNS, and appropriate authentication remains future work.

## INC-012 — Terraform Generated Files in Git Repository

**Status:** Resolved

**Symptoms:** Terraform generated binary plan files and readable plan output existed under `infrastructure/terraform/`.

**Risk:** Terraform plans may contain sensitive infrastructure configuration and must not be published indiscriminately.

**Resolution:** Added `.gitignore` exclusions for `*.tfplan`, generated plan text, Terraform state, and local Terraform working directories.

**Verification:** `git check-ignore` confirmed the relevant plan files were excluded. No Terraform plan files were included in the documentation commit.

## INC-013 — Documentation Terminal Paste Corruption

**Status:** Mitigated

**Symptoms:** Long terminal paste operations occasionally produced visibly malformed command text.

**Action taken:** Used smaller commands and verified generated Markdown files after creation.

**Verification:** HLD, LLD, deployment guide, and demo guide were created. The demo document contained the expected section headings.

**Lesson:** Verify generated files rather than assuming successful command execution guarantees complete document integrity.

---

## Final Validation and Remaining Risks

- Automated test suite: 30 tests passed in the last verified local run.
- Backend and frontend Kubernetes Deployments: previously observed Ready.
- AWS inference: previously verified using the Iris classifier.
- EKS managed node-group failure: unresolved.
- Production high availability: not implemented.
- Shared organization-internal application URL: not implemented.
- Artifact filesystem permission hardening: pending.
- Remote GitHub Actions execution: not yet verified.
- AWS resource cleanup: pending explicit authorization.

## Documentation Policy

This incident history distinguishes observed symptoms, confirmed causes, mitigations, and unresolved issues. Where the exact original error message or command history is unavailable, the document does not claim to reproduce it verbatim.
