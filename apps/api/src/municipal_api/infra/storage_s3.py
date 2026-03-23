import boto3
from botocore.client import Config
from municipal_api.infra.settings import settings

def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
        verify=settings.s3_secure,
    )

def ensure_bucket_exists():
    s3 = s3_client()
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if settings.s3_bucket not in buckets:
        s3.create_bucket(Bucket=settings.s3_bucket)
