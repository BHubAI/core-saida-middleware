from functools import lru_cache
from typing import Optional

import boto3
from core.config import settings


@lru_cache(maxsize=1)
def get_s3_client():
    """
    Get an S3 client.

    Returns:
        boto3.client: S3 client
    """

    params = {
        "region_name": settings.AWS_REGION,
    }

    if settings.AWS_ENDPOINT_URL:
        params["endpoint_url"] = settings.AWS_ENDPOINT_URL

    return boto3.client("s3", **params)


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
        response = get_s3_client().get_object(Bucket=bucket_name, Key=object_key)
        content = response["Body"].read().decode("utf-8")
        return content
    except Exception as e:
        print(f"Error getting object from S3: {e}")
        return None
