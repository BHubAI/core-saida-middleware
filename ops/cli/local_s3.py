#!/usr/bin/env python3
import argparse
import logging
import os
from typing import List, Optional

import boto3


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Get environment variables
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-2")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    region_name=REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)


def create_bucket(bucket_name: str) -> bool:
    """Create a new S3 bucket."""
    try:
        s3_client.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": REGION}
        )
        logger.info(f"Bucket '{bucket_name}' created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating bucket '{bucket_name}': {str(e)}")
        return False


def list_buckets() -> List[str]:
    """List all S3 buckets."""
    try:
        response = s3_client.list_buckets()
        buckets = [bucket["Name"] for bucket in response["Buckets"]]
        logger.info(f"Found {len(buckets)} buckets: {', '.join(buckets)}")
        return buckets
    except Exception as e:
        logger.error(f"Error listing buckets: {str(e)}")
        return []


def delete_bucket(bucket_name: str) -> bool:
    """Delete an S3 bucket."""
    try:
        # First, delete all objects in the bucket
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        if "Contents" in objects:
            for obj in objects["Contents"]:
                s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
                logger.info(f"Deleted object '{obj['Key']}' from bucket '{bucket_name}'")

        # Then delete the bucket
        s3_client.delete_bucket(Bucket=bucket_name)
        logger.info(f"Bucket '{bucket_name}' deleted successfully")
        return True
    except Exception as e:
        logger.error(f"Error deleting bucket '{bucket_name}': {str(e)}")
        return False


def put_object(
    bucket_name: str,
    object_key: str,
    file_path: Optional[str] = None,
    content: Optional[str] = None,
) -> bool:
    """Put an object in an S3 bucket."""
    try:
        if file_path:
            with open(file_path, "rb") as file:
                s3_client.upload_fileobj(file, bucket_name, object_key)
            logger.info(f"File '{file_path}' uploaded to '{bucket_name}/{object_key}'")
        elif content:
            s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=content)
            logger.info(f"Content uploaded to '{bucket_name}/{object_key}'")
        else:
            logger.error("Either file_path or content must be provided")
            return False
        return True
    except Exception as e:
        logger.error(f"Error uploading to '{bucket_name}/{object_key}': {str(e)}")
        return False


def remove_object(bucket_name: str, object_key: str) -> bool:
    """Remove an object from an S3 bucket."""
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        logger.info(f"Object '{object_key}' removed from bucket '{bucket_name}'")
        return True
    except Exception as e:
        logger.error(f"Error removing object '{object_key}' from bucket '{bucket_name}': {str(e)}")
        return False


def list_objects(bucket_name: str, prefix: Optional[str] = None) -> List[str]:
    """List objects in an S3 bucket."""
    try:
        params = {"Bucket": bucket_name}
        if prefix:
            params["Prefix"] = prefix

        response = s3_client.list_objects_v2(**params)
        objects = []

        if "Contents" in response:
            objects = [obj["Key"] for obj in response["Contents"]]
            logger.info(f"Found {len(objects)} objects in bucket '{bucket_name}'")
            for obj in objects:
                logger.info(f"  - {obj}")
        else:
            logger.info(f"No objects found in bucket '{bucket_name}'")

        return objects
    except Exception as e:
        logger.error(f"Error listing objects in bucket '{bucket_name}': {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(description="S3 operations with LocalStack")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create bucket command
    create_parser = subparsers.add_parser("create-bucket", help="Create a new S3 bucket")
    create_parser.add_argument("bucket_name", help="Name of the bucket to create")

    # List buckets command
    subparsers.add_parser("list-buckets", help="List all S3 buckets")

    # Delete bucket command
    delete_parser = subparsers.add_parser("delete-bucket", help="Delete an S3 bucket")
    delete_parser.add_argument("bucket_name", help="Name of the bucket to delete")

    # Put object comma
    put_parser = subparsers.add_parser("put-object", help="Put an object in an S3 bucket")
    put_parser.add_argument("bucket_name", help="Name of the bucket")
    put_parser.add_argument("object_key", help="Key of the object")
    put_parser.add_argument("--file", help="Path to the file to upload")
    put_parser.add_argument("--content", help="Content to upload as a string")

    # Remove object command
    remove_parser = subparsers.add_parser(
        "remove-object", help="Remove an object from an S3 bucket"
    )
    remove_parser.add_argument("bucket_name", help="Name of the bucket")
    remove_parser.add_argument("object_key", help="Key of the object to remove")

    # List objects command
    list_objects_parser = subparsers.add_parser("list-objects", help="List objects in an S3 bucket")
    list_objects_parser.add_argument("bucket_name", help="Name of the bucket")
    list_objects_parser.add_argument("--prefix", help="Prefix to filter objects")

    args = parser.parse_args()

    if args.command == "create-bucket":
        create_bucket(args.bucket_name)
    elif args.command == "list-buckets":
        list_buckets()
    elif args.command == "delete-bucket":
        delete_bucket(args.bucket_name)
    elif args.command == "put-object":
        put_object(args.bucket_name, args.object_key, args.file, args.content)
    elif args.command == "remove-object":
        remove_object(args.bucket_name, args.object_key)
    elif args.command == "list-objects":
        list_objects(args.bucket_name, args.prefix)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
