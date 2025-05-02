# src/utils/io.py
"""
I/O utilities for billing aggregation pipeline.
Provides functions to read lines from local filesystem or S3.
"""
import os
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def read_lines(path: str) -> list[str]:
    """
    Read all lines from a text file specified by a local path or an S3 URI.

    Args:
        path (str): Local filesystem path or S3 URI (e.g. 's3://bucket/key').

    Returns:
        list[str]: List of lines read from the file (without trailing newlines).

    Raises:
        FileNotFoundError: If the local file does not exist.
        ClientError, BotoCoreError: If S3 retrieval fails.
    """
    if path.startswith("s3://"):
        parsed = urlparse(path)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
            content = obj['Body'].read().decode('utf-8')
        except (ClientError, BotoCoreError) as e:
            raise
        return content.splitlines()
    else:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Local file not found: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().splitlines()
