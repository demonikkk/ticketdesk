# TicketDesk

A lightweight IT support ticket tracker built with **FastAPI** and **PostgreSQL**, deployed on **AWS** with **Terraform** and a **GitHub Actions** CI/CD pipeline.

Users raise support tickets (with optional file attachments), and support staff (admins) work them through **Open → In Progress → Resolved → Closed**.

> Team 8: Nikhil Kumar, Abdullah, Sibu Pradhan
> Repository: https://github.com/demonikkk/ticketdesk

---

## Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Tech stack](#tech-stack)
4. [Project structure](#project-structure)
5. [Configuration](#configuration)
6. [Run locally](#run-locally)
7. [Tests](#tests)
8. [Deploy to AWS](#deploy-to-aws)
9. [CI/CD pipeline](#cicd-pipeline)
10. [Security](#security)
11. [Operations](#operations)
12. [Troubleshooting](#troubleshooting)

---

## Features

| Feature | Details |
|---|---|
| Authentication | Registration and login, bcrypt-hashed passwords, signed session cookies |
| Tickets | Create tickets with title, description and priority (Low, Medium, High) |
| Status workflow | Open → In Progress → Resolved → Closed (admin only) |
| Role-based access | **Users** see only their own tickets. **Admins** see all tickets and change status. |
| Attachments | Upload png, jpg, jpeg, pdf or txt files (max 5 MB), stored in S3 on AWS |
| Dashboard | Ticket counts by status and by priority |
| Serverless processing | Each uploaded file triggers a Lambda function that logs the file details |
| Health check | `GET /health` returns `{"status": "ok"}` |

API documentation is generated automatically at `/docs`.

## Architecture

```
                          Internet
                             │ HTTP :80
                             ▼
┌──────────────── VPC 10.0.0.0/16 (us-east-1) ─────────────────┐
│  Public subnets                                              │
│  ┌────────────────────────────────────────────┐              │
│  │ EC2 t3.micro: Docker container (FastAPI)   │── IAM role   │
│  │ Security group: HTTP 80 only, no SSH       │              │
│  └──────────┬─────────────────────────────────┘              │
│             │ TCP 5432 (from app security group only)        │
│  Private subnets                                             │
│  ┌──────────▼──────────┐                                     │
│  │ RDS PostgreSQL 16   │  not publicly accessible            │
│  └─────────────────────┘                                     │
└──────────────────────────────────────────────────────────────┘

EC2 ──► S3 (private bucket) ──ObjectCreated──► Lambda ──► CloudWatch Logs
EC2 ──► Secrets Manager (DB credentials, app secrets)
GitHub Actions ──(OIDC, no stored keys)──► ECR ──► EC2 (redeploy via SSM)
```

| AWS service | Purpose |
|---|---|
| VPC | Public subnets for the app, private subnets for the database, no NAT Gateway |
| EC2 | Runs the application container (Amazon Linux 2023, IMDSv2 required) |
| RDS | PostgreSQL 16, encrypted, private |
| S3 | Private, encrypted bucket for attachments |
| Lambda | Processes S3 object-created events |
| Secrets Manager | Database connection details, session key, admin password |
| ECR | Stores the application image |
| IAM | Least-privilege roles for EC2, Lambda and the GitHub deploy role |
| Systems Manager | Shell access (no SSH) and pipeline-triggered redeploys |
| CloudWatch | Application and Lambda logs (7-day retention) |

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, boto3 |
| Database | PostgreSQL 16 (local: Docker, AWS: RDS) |
| Frontend | Server-rendered Jinja2 templates |
| Storage | Local folder in development, Amazon S3 on AWS |
| Containers | Docker, Docker Compose |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |
| Tests | pytest |

## Project structure

```
ticketdesk/
├── app/
│   ├── main.py            routes, authentication, role checks
│   ├── config.py          settings read from environment variables
│   ├── database.py        SQLAlchemy engine and session
│   ├── models.py          User, Ticket, Attachment
│   ├── security.py        password hashing
│   ├── storage.py         local and S3 storage backends
│   └── templates/         HTML pages
├── scripts/
│   └── set_password.py    reset a user's password
├── tests/                 pytest suite (12 tests)
├── terraform/
│   ├── main.tf, variables.tf, outputs.tf, versions.tf
│   ├── terraform.tfvars.example
│   └── modules/           network, rds, s3, ecr, ec2, lambda, cicd
├── .github/workflows/ci.yaml
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── .env.example
```

## Configuration

All configuration comes from environment variables. **No secrets are stored in the repository.**

| Variable | Description | Example |
|---|---|---|
| `POSTGRES_USER` | Local database user | `ticketdesk` |
| `POSTGRES_PASSWORD` | Local database password | `change_me` |
| `POSTGRES_DB` | Local database name | `ticketdesk` |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg2://user:pass@localhost:5432/ticketdesk` |
| `SECRET_KEY` | Signs the session cookies | a long random string |
| `ADMIN_USERNAME` | Admin account created at first start-up | `admin` |
| `ADMIN_PASSWORD` | Password for that admin account | `change_me_too` |
| `STORAGE_BACKEND` | `local` or `s3` | `local` |
| `LOCAL_STORAGE_DIR` | Upload folder when the backend is `local` | `./uploads` |
| `S3_BUCKET` | Bucket name when the backend is `s3` | `ticketdesk-attachments` |
| `S3_ENDPOINT_URL` | Optional custom S3 endpoint (leave empty on AWS) | empty |
| `AWS_REGION` | AWS region | `us-east-1` |
| `MAX_UPLOAD_MB` | Maximum attachment size | `5` |

On AWS these values are supplied by the deployment script from Secrets Manager. S3 access uses the EC2 instance role, so no AWS keys are used.

## Run locally

**Prerequisites:** Python 3.12, Docker Desktop, Git.

```bash
# 1. Clone
git clone https://github.com/demonikkk/ticketdesk.git
cd ticketdesk

# 2. Virtual environment
python -m venv venv
source venv/bin/activate          # Git Bash on Windows: source venv/Scripts/activate
                                  # PowerShell: venv\Scripts\Activate.ps1

# 3. Dependencies
pip install -r requirements-dev.txt

# 4. Configuration (edit the values in .env)
cp .env.example .env

# 5. Database
docker compose up -d db

# 6. Application
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000. Log in with the admin credentials from `.env`, or register a new user.

**Run everything in containers:**

```bash
docker compose up --build
```

## Tests

```bash
pytest -v
```

The suite has 12 tests covering health, login protection, registration validation, ticket creation, the status flow, role restrictions (users cannot change status or see other users' tickets), admin visibility, dashboard counts and attachment validation. It uses a temporary SQLite database and mocks file storage, so no database or AWS account is needed.

## Deploy to AWS

**Prerequisites:** an AWS account and CLI credentials (`aws configure`), Terraform 1.5 or later, Docker, Git.

**1. Configure Terraform**

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set `github_subject` to your repository's OIDC subject, in the form:

```
repo:OWNER@OWNER_ID/REPO@REPO_ID:ref:refs/heads/main
```

If you use a different AWS account, also update the role ARN in the `deploy` job of `.github/workflows/ci.yaml`.

**2. Create the infrastructure**

```bash
terraform init
terraform plan
terraform apply
```

The plan creates 42 resources. RDS takes about 5 to 10 minutes. Note the outputs:

```bash
terraform output app_url
terraform output instance_id
```

**3. Publish the application image**

The registry is empty after a fresh apply. Either push a commit to `main` (the pipeline builds, pushes and deploys, after you set the `INSTANCE_ID` repository variable), or do it by hand from the project root:

```bash
REPO=$(terraform -chdir=terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${REPO%%/*}
docker build --platform linux/amd64 -t $REPO:latest .
docker push $REPO:latest
```

Then open the instance in the EC2 console, choose Connect, then Session Manager, and run:

```bash
sudo /usr/local/bin/deploy.sh
sudo docker ps
```

**4. Log in**

The admin password is generated by Terraform and stored in Secrets Manager:

```bash
aws secretsmanager get-secret-value --secret-id ticketdesk/app --query SecretString --output text
```

Open the `app_url` output, log in as `admin` with the `admin_password` value, and register a normal user to test the full flow.

**5. Clean up**

```bash
cd terraform
terraform destroy
```

The EC2 instance and the database are billed by the hour while they exist, so destroy the stack when you are finished.

## CI/CD pipeline

`.github/workflows/ci.yaml` runs on every push to `main` and on pull requests.

| Job | What it does |
|---|---|
| `test` | Installs dependencies and runs `pytest -v` |
| `docker-build` | Builds the Docker image to verify it (after `test`) |
| `deploy` | On pushes to `main` only: assumes an AWS role through **OIDC**, builds and pushes the image to ECR, then runs `deploy.sh` on the EC2 instance through SSM |

**Repository variable required:** `INSTANCE_ID`, the EC2 instance ID from `terraform output instance_id`. Update it whenever the infrastructure is recreated.

No AWS keys are stored in GitHub. The deploy role trusts only the `main` branch of this repository and can only push to the one ECR repository and run one command on the one instance.

## Security

- **No secrets in Git.** `.env`, `*.tfvars`, `*.tfstate` and `*.log` are ignored. Only `.env.example` and `terraform.tfvars.example` with placeholders are committed.
- **Secrets Manager.** The database password, session key and admin password are generated by Terraform and stored in Secrets Manager.
- **Private database.** RDS is not publicly accessible and accepts connections only from the application's security group.
- **Least-privilege IAM.** Each role is limited to named resources: the EC2 role reads two secrets, uses one bucket, pulls one repository and writes to one log group. The Lambda role can only write logs.
- **Network.** Only port 80 is open on the app server. There is no SSH, and access goes through Session Manager.
- **Hardening.** IMDSv2 is required, volumes are encrypted, S3 blocks all public access, the container runs as a non-root user, and uploads are restricted by file type and size.
- **Access control.** Users can see and open only their own tickets and attachments, and only admins can change ticket status.

## Operations

| Task | Command |
|---|---|
| Restart the app (on EC2) | `sudo docker restart ticketdesk` |
| Redeploy the latest image (on EC2) | `sudo /usr/local/bin/deploy.sh` |
| View container logs (on EC2) | `sudo docker logs ticketdesk` |
| Application logs | CloudWatch log group `/ticketdesk/app` |
| Lambda logs | CloudWatch log group `/aws/lambda/ticketdesk-file-processor` |
| Reset a user's password | `python -m scripts.set_password <username>` (run locally against the database) |

The container uses `--restart unless-stopped`, so it comes back automatically after a crash or an instance reboot.

## Troubleshooting

| Problem | Fix |
|---|---|
| `pytest` is not recognized | Activate the virtual environment first |
| `pip install` fails on `pyyaml` | Use Python 3.12 |
| Terraform asks for variable values | Run Terraform commands from the `terraform/` folder, not from `terraform/modules/` |
| Pipeline fails with "Not authorized to perform sts:AssumeRoleWithWebIdentity" | The `github_subject` does not match the token GitHub sends. Read the exact subject from a failed event in CloudTrail (`userName` field) and update `terraform.tfvars`. |
| Pipeline `deploy` job cannot find the instance | Update the `INSTANCE_ID` repository variable after recreating the infrastructure |
| Cannot log in on AWS with a local account | The AWS database is separate from the local one. Register the account again. |
| Page does not load after deploy | Run `sudo docker logs ticketdesk` in Session Manager |

## Team

| Name | Team |
|---|---|
| Nikhil Kumar | Team 8 |
| Abdullah | Team 8 |
| Sibu Pradhan | Team 8 |