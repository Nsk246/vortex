from pathlib import Path
import tempfile
import boto3
from botocore.client import Config
from .config import get_settings


settings = get_settings()


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def download_to_temp(storage_key: str, suffix: str = "") -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()
    s3_client().download_file(settings.s3_bucket, storage_key, tmp.name)
    return Path(tmp.name)

def upload_artifact(storage_key: str, path: Path, content_type: str) -> None:
    s3_client().upload_file(
        str(path),
        settings.s3_bucket,
        storage_key,
        ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"},
    )

