#!/usr/bin/env python3
"""
S3 MCP Server - Access AWS S3 resources using boto3.

This server provides access to S3 functionality through
the Model Context Protocol (MCP), enabling AI assistants and other tools to
interact with AWS S3.

"""

import json
import logging
import os
from typing import Any, Optional

import boto3
from botocore.client import BaseClient  # Import BaseClient for type hinting
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
        boto3.client: S3 client

    Raises:
        NoCredentialsError: If AWS credentials are not found.
    """
    global s3_client

    if s3_client is None:
        logger.info("Initializing S3 client")
        # boto3 will automatically look for credentials in environment variables
        # (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or other configuration.
        try:
            s3_client = boto3.client("s3")
            # A simple check to see if credentials are valid by making a low-impact call
            s3_client.list_buckets()
            logger.info("Successfully initialized and validated S3 client.")
        except NoCredentialsError:
            logger.error("Failed to find AWS credentials. Please configure them.")
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during S3 client initialization: {e}"
            )
            raise

    return s3_client


def format_response(data: Any) -> str:
    """Format response data as JSON string.

    Args:
        data: Data to format

    Returns:
        str: JSON formatted string
    """
    return json.dumps(data, indent=2, default=str)


# BUCKET MANAGEMENT
def _list_buckets_logic() -> dict:
    """Core logic to list S3 buckets."""
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


def main():
    """Main entry point for uv execution."""
    logger.info("Starting S3 MCP Server")

    # Log configuration
    aws_region = os.getenv("AWS_DEFAULT_REGION", "Not specified (will use default)")
    logger.info(f"AWS Region: {aws_region}")

    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
