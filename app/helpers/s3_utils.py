from typing import Optional

import boto3
from core.config import settings


# Get environment variables
ENDPOINT_URL = settings.AWS_ENDPOINT_URL
REGION = settings.AWS_REGION

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    region_name=REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)


def get_object(bucket_name: str, object_key: str) -> Optional[str]:
    """
    Read an object from an S3 bucket.

    Args:
        bucket_name: Name of the S3 bucket
        object_key: Key of the object to read

    Returns:
        Optional[str]: Content of the object if successful, None otherwise
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response["Body"].read().decode("utf-8")
        return content
    except Exception:
        return None
