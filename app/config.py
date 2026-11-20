import os
from dotenv import load_dotenv

load_dotenv()  # does not override variables already set in the environment

DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
S3_BUCKET = os.environ.get("S3_BUCKET", "ticketdesk-attachments")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL") or None  # empty on real AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "s3")   # "local" or "s3"
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR", "./uploads")
