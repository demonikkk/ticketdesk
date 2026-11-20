from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from . import config

_client = None


def _is_local() -> bool:
    return config.STORAGE_BACKEND == "local"


def _local_path(key: str) -> Path:
    root = Path(config.LOCAL_STORAGE_DIR).resolve()
    path = (root / key).resolve()
    if root not in path.parents:
        raise ValueError("Invalid storage key")
    return path


def client():
    global _client
    if _client is None:
        kwargs = {"region_name": config.AWS_REGION}
        if config.S3_ENDPOINT_URL:  # only for S3-compatible emulators
            kwargs["endpoint_url"] = config.S3_ENDPOINT_URL
            kwargs["config"] = Config(s3={"addressing_style": "path"})
        # Credentials: the EC2 IAM role on AWS (never keys in code).
        _client = boto3.client("s3", **kwargs)
    return _client


def init():
    """Called at startup."""
    if _is_local():
        Path(config.LOCAL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    elif config.S3_ENDPOINT_URL:
        try:
            client().head_bucket(Bucket=config.S3_BUCKET)
        except ClientError:
            client().create_bucket(Bucket=config.S3_BUCKET)
    # On real AWS the bucket is created by Terraform.


def upload_file(key: str, data: bytes, content_type: str | None):
    if _is_local():
        path = _local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return
    client().put_object(
        Bucket=config.S3_BUCKET, Key=key, Body=data,
        ContentType=content_type or "application/octet-stream",
    )


def stream(key: str):
    """Return an iterator of byte chunks for the stored file."""
    if _is_local():
        def gen():
            with open(_local_path(key), "rb") as f:
                while chunk := f.read(65536):
                    yield chunk
        return gen()
    return client().get_object(Bucket=config.S3_BUCKET, Key=key)["Body"].iter_chunks()