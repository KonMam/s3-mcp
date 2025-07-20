"""
S3 MCP Server - Access AWS S3 resources using boto3.

This server provides access to S3 functionality through
the Model Context Protocol (MCP), enabling AI assistants and other tools to
interact with AWS S3.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Union

import boto3
from botocore.client import BaseClient
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG") else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("S3 MCP Server")

# Global S3 client
s3_client: Optional[BaseClient] = None


def get_s3_client() -> BaseClient:
    """Get or create the S3 boto3 client.

    Returns:
        BaseClient: S3 client

    Raises:
        NoCredentialsError: If AWS credentials are not found.
    """
    global s3_client

    if s3_client is None:
        logger.info("Initializing S3 client")
        try:
            s3_client = boto3.client("s3")
            s3_client.list_buckets()  # Validate credentials
            logger.info("Successfully initialized and validated S3 client.")
        except NoCredentialsError as e:
            logger.error("AWS credentials not found.")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error initializing S3 client: {e}")
            raise e

    return s3_client


def format_response(data: Any) -> str:
    """Format response data as JSON string.

    Args:
        data (Any): Data to format

    Returns:
        str: JSON formatted string
    """
    return json.dumps(data, indent=2, default=str)


# BUCKET MANAGEMENT
def _list_buckets_logic() -> Dict[str, Any]:
    """Core logic to list S3 buckets.

    Returns:
        Dict[str, Any]: Raw boto3 response from list_buckets.
    """
    client = get_s3_client()
    return client.list_buckets()


@mcp.tool()
def list_buckets() -> str:
    """Lists all buckets in the AWS account.

    Returns:
        str: JSON formatted list of buckets.
    """
    result = _list_buckets_logic()
    return format_response(result)


# OBJECT MANAGEMENT
def _put_object_logic(
    bucket: str,
    key: str,
    body: Union[str, bytes],
) -> Dict[str, Any]:
    """Core logic to put an object into an S3 bucket.

    Args:
        bucket (str): The S3 bucket name.
        key (str): The S3 object key.
        body (Union[str, bytes]): The content or file path.

    Returns:
        Dict[str, Any]: Raw boto3 response from put_object.
    """
    client = get_s3_client()
    params: Dict[str, Any] = {"Bucket": bucket, "Key": key}

    if isinstance(body, str) and os.path.exists(body) and os.path.isfile(body):
        with open(body, "rb") as f:
            params["Body"] = f.read()
    elif isinstance(body, str):
        params["Body"] = body.encode("utf-8")
    else:
        params["Body"] = body  # Assuming bytes or file-like object

    return client.put_object(**params)


@mcp.tool()
def put_object(
    bucket: str,
    key: str,
    body: str,
) -> str:
    """Puts an object into an S3 bucket.

    Args:
        bucket (str): The name of the bucket.
        key (str): The key (name) of the object.
        body (str): The content of the object or absolute file path.

    Returns:
        str: JSON formatted S3 response.
    """
    result = _put_object_logic(bucket=bucket, key=key, body=body)
    return format_response(result)


def _get_object_logic(bucket: str, key: str) -> Dict[str, Any]:
    """Core logic to get an object from an S3 bucket.

    Args:
        bucket (str): The S3 bucket name.
        key (str): The S3 object key.

    Returns:
        Dict[str, Any]: Raw boto3 response from get_object.
    """
    client = get_s3_client()
    response = client.get_object(Bucket=bucket, Key=key)
    # The body is a StreamingBody, which is not directly JSON serializable.
    # We read it and decode it to a string.
    if 'Body' in response:
        response['Body'] = response['Body'].read().decode('utf-8')
    return response


@mcp.tool()
def get_object(bucket: str, key: str) -> str:
    """Gets an object from an S3 bucket.

    Args:
        bucket (str): The name of the bucket.
        key (str): The key (name) of the object.

    Returns:
        str: JSON formatted S3 response.
    """
    result = _get_object_logic(bucket=bucket, key=key)
    return format_response(result)


def _delete_object_logic(bucket: str, key: str) -> Dict[str, Any]:
    """Core logic to delete an object from an S3 bucket.

    Args:
        bucket (str): The S3 bucket name.
        key (str): The S3 object key.

    Returns:
        Dict[str, Any]: Raw boto3 response from delete_object.
    """
    client = get_s3_client()
    return client.delete_object(Bucket=bucket, Key=key)


@mcp.tool()
def delete_object(bucket: str, key: str) -> str:
    """Deletes an object from an S3 bucket.

    Args:
        bucket (str): The name of the bucket.
        key (str): The key (name) of the object.

    Returns:
        str: JSON formatted S3 response.
    """
    result = _delete_object_logic(bucket=bucket, key=key)
    return format_response(result)


def _list_objects_v2_logic(
    bucket: str,
    prefix: Optional[str] = None,
    max_keys: Optional[int] = None,
    continuation_token: Optional[str] = None,
    delimiter: Optional[str] = None,
) -> Dict[str, Any]:
    """Core logic to list objects in an S3 bucket.

    Args:
        bucket (str): The S3 bucket name.
        prefix (Optional[str]): Filter for keys starting with this prefix.
        max_keys (Optional[int]): Maximum number of keys to return.
        continuation_token (Optional[str]): Token for paginating results.
        delimiter (Optional[str]): Delimiter for grouping keys.

    Returns:
        Dict[str, Any]: Raw boto3 response from list_objects_v2.
    """
    client = get_s3_client()
    params: Dict[str, Any] = {"Bucket": bucket}
    if prefix:
        params["Prefix"] = prefix
    if max_keys:
        params["MaxKeys"] = max_keys
    if continuation_token:
        params["ContinuationToken"] = continuation_token
    if delimiter:
        params["Delimiter"] = delimiter
    return client.list_objects_v2(**params)


@mcp.tool()
def list_objects_v2(
    bucket: str,
    prefix: Optional[str] = None,
    max_keys: Optional[int] = None,
    continuation_token: Optional[str] = None,
    delimiter: Optional[str] = None,
) -> str:
    """Lists objects in an S3 bucket.

    Args:
        bucket (str): The name of the bucket.
        prefix (Optional[str]): Filter for keys starting with this prefix.
        max_keys (Optional[int]): Maximum number of keys to return.
        continuation_token (Optional[str]): Token for paginating results.
        delimiter (Optional[str]): Delimiter for grouping keys.

    Returns:
        str: JSON formatted S3 response.
    """
    result = _list_objects_v2_logic(
        bucket=bucket,
        prefix=prefix,
        max_keys=max_keys,
        continuation_token=continuation_token,
        delimiter=delimiter,
    )
    return format_response(result)


def _head_object_logic(
    bucket: str,
    key: str,
    if_match: Optional[str] = None,
    if_none_match: Optional[str] = None,
    version_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core logic to retrieve metadata from an object.

    Args:
        bucket (str): The S3 bucket name.
        key (str): The S3 object key.
        if_match (Optional[str]): Return object only if its ETag is the same.
        if_none_match (Optional[str]): Return object only if its ETag is different.
        version_id (Optional[str]): Version of the object.

    Returns:
        Dict[str, Any]: Raw boto3 response from head_object.
    """
    client = get_s3_client()
    params: Dict[str, Any] = {"Bucket": bucket, "Key": key}
    if if_match:
        params["IfMatch"] = if_match
    if if_none_match:
        params["IfNoneMatch"] = if_none_match
    if version_id:
        params["VersionId"] = version_id
    return client.head_object(**params)


@mcp.tool()
def head_object(
    bucket: str,
    key: str,
    if_match: Optional[str] = None,
    if_none_match: Optional[str] = None,
    version_id: Optional[str] = None,
) -> str:
    """Retrieves metadata from an object without returning the object itself.

    Args:
        bucket (str): The name of the bucket.
        key (str): The key (name) of the object.
        if_match (Optional[str]): Return object only if its ETag is the same.
        if_none_match (Optional[str]): Return object only if its ETag is different.
        version_id (Optional[str]): Version of the object.

    Returns:
        str: JSON formatted S3 response.
    """
    result = _head_object_logic(
        bucket=bucket,
        key=key,
        if_match=if_match,
        if_none_match=if_none_match,
        version_id=version_id,
    )
    return format_response(result)


def _upload_file_logic(
    filename: str,
    bucket: str,
    key: str,
    extra_args: Optional[Dict[str, Any]] = None,
) -> None:
    """Core logic to upload a file to an S3 bucket.

    Args:
        filename (str): The path to the file to upload.
        bucket (str): The S3 bucket name.
        key (str): The S3 object key.
        extra_args (Optional[Dict[str, Any]]): Extra arguments for the upload.
    """
    client = get_s3_client()
    client.upload_file(
        Filename=filename,
        Bucket=bucket,
        Key=key,
        ExtraArgs=extra_args,
    )


@mcp.tool()
def upload_file(
    filename: str,
    bucket: str,
    key: str,
) -> str:
    """Uploads a file to an S3 object.

    Args:
        filename (str): The path to the file to upload.
        bucket (str): The name of the bucket to upload to.
        key (str): The name of the key to upload to.

    Returns:
        str: JSON formatted success message.
    """
    _upload_file_logic(filename=filename, bucket=bucket, key=key)
    return format_response(
        {"status": "success", "message": f"File '{filename}' uploaded to '{bucket}/{key}'."}
    )


def main() -> None:
    """Main entry point for execution."""
    logger.info("Starting S3 MCP Server")
    aws_region = os.getenv("AWS_DEFAULT_REGION", "Not specified (using default)")
    logger.info(f"AWS Region: {aws_region}")

    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
