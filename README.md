# TicketDesk

A lightweight IT support ticket tracker built with **FastAPI** and **PostgreSQL**, designed to be deployed on AWS (EC2, RDS, S3, Lambda) with Terraform and GitHub Actions.

## Features

- User registration and login (session-based, bcrypt password hashing)
- Create tickets with title, description and priority (Low / Medium / High)
- File attachments per ticket (png, jpg, jpeg, pdf, txt; max 5 MB)
- Status flow: Open -> In Progress -> Resolved -> Closed
- Role-based access control:
  - **user**: creates tickets, sees only their own tickets and attachments
  - **admin (support)**: sees all tickets, changes ticket status
- Dashboard with ticket counts by status and priority
- `/health` endpoint for monitoring and load balancer checks

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Database | PostgreSQL 16 (local: Docker, AWS: RDS) |
| Storage | Local folder in development, Amazon S3 on AWS |
| Frontend | Server-rendered Jinja2 templates |
| Container | Docker, Docker Compose |
| Tests | pytest |
| CI/CD | GitHub Actions |
| Infrastructure | Terraform |

## Project structure

```
ticketdesk/
├── app/
│   ├── main.py          # routes, auth, RBAC
│   ├── config.py        # settings read from environment variables
│   ├── database.py      # SQLAlchemy engine and session
│   ├── models.py        # User, Ticket, Attachment
│   ├── security.py      # password hashing
│   ├── storage.py       # local / S3 storage backend
│   └── templates/       # HTML templates
├── scripts/
│   └── set_password.py  # reset a user's password
├── tests/               # pytest test suite
├── .github/workflows/   # CI pipeline
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── .env.example         # template for local configuration
```

## Configuration

All configuration comes from environment variables. No secrets are stored in the repository.

| Variable | Description | Example |
|---|---|---|
| `POSTGRES_USER` | Local database user | `ticketdesk` |
| `POSTGRES_PASSWORD` | Local database password | `change_me` |
| `POSTGRES_DB` | Local database name | `ticketdesk` |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg2://user:pass@localhost:5432/ticketdesk` |
| `SECRET_KEY` | Key used to sign session cookies | long random string |
| `ADMIN_USERNAME` | Admin account created at first startup | `admin` |
| `ADMIN_PASSWORD` | Password for that admin account | `change_me_too` |
| `STORAGE_BACKEND` | `local` or `s3` | `local` |
| `LOCAL_STORAGE_DIR` | Upload folder when backend is `local` | `./uploads` |
| `S3_BUCKET` | Bucket name when backend is `s3` | `ticketdesk-attachments` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `MAX_UPLOAD_MB` | Maximum attachment size | `5` |

On AWS, S3 access uses the EC2 instance IAM role. No AWS access keys are used.

## Run locally

Prerequisites: Python 3.12, Docker Desktop, Git.

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd ticketdesk

# 2. Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate      # Git Bash on Windows
# source venv/bin/activate        # Linux / macOS
# venv\Scripts\Activate.ps1       # PowerShell

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Create your local config and edit the values
cp .env.example .env

# 5. Start PostgreSQL
docker compose up -d db

# 6. Run the app
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000. Log in with the admin credentials from `.env`, or register a new user. Interactive API docs are at `/docs`.

## Run everything in containers

```bash
docker compose up --build
```

The app is available at http://localhost:8000.

## Tests

```bash
pytest -v
```

The tests use a temporary SQLite database and mock file storage, so they need no running services.

## Reset a user's password

```bash
python -m scripts.set_password <username>
```

## Docs and deployment

The sections below are completed as the AWS deployment progresses.

- Architecture diagram: _to be added_
- Terraform structure and deployment steps: _to be added_
- CI/CD pipeline: _to be added_
- Test scenarios and results: _to be added_
- `terraform destroy` evidence: _to be added_

## Author

Nikhil Kumar
