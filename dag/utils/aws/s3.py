"""S3-related utility functions."""
import os
from functools import wraps
from pathlib import Path
from typing import Any, BinaryIO, Callable, Generator

import boto3
from boto3.s3.transfer import S3Transfer

_S3 = None


def get_s3() -> boto3.resource:
    """Get the s3 resource."""
    global _S3
    if _S3 is None:
        _S3 = boto3.resource("s3", endpoint_url=os.getenv("AWS_ENDPOINT_URL"))
    return _S3


def get_client() -> boto3.client:
    """Get a client for s3."""
    s3 = get_s3()
    return s3.meta.client


def parse_path(func: Callable) -> Callable:
    """Decorate function to accept path argument.

    Parse an optionally provided path and pass bucket and prefix/key
    arguments to the underlying function.

    This can be utilized by passing `path` as a keyword argument.

    The first two arguments of the underlying function must be bucket and
    prefix/key, respectively.
    """

    @wraps(func)
    def wrapper(
        bucket: str = None,
        prefix: str = None,
        key: str = None,
        *,
        path: str = None,
        **kwargs: Any
    ) -> Any:
        if path:
            path = path.lstrip("s3://")
            parsed_bucket, *parsed_prefix = path.split(os.sep)
            parsed_prefix = "/".join(parsed_prefix) if parsed_prefix else None
        else:
            parsed_bucket = None
            parsed_prefix = None
        return func(bucket or parsed_bucket, prefix or key or parsed_prefix, **kwargs)

    return wrapper


@parse_path
def iter_keys(
    bucket: str = None, prefix: str = None, *, path: str = None
) -> Generator[str, None, None]:
    """Iterate keys for a given bucket / prefix.

    The native `list_objects` method in boto is limited to the first
    1000 objects. This iterates over the paginated results.

    Note: This is distinct from the native aws s3 list_objects method which
    filters by the bucket / prefix, but keys are returned with the prefix
    prepended. Here, the keys are relative to the prefix if it is provided.

    Args:
        bucket (str, optional): S3 bucket name
        prefix (str, optional): S3 prefix. Defaults to None
        path (str, optional): Optional path that can be provided
            instead of separate bucket / prefix. Defaults to None

    Returns:
        Generator[str]: Yields key names
    """
    assert bucket, "Either `bucket` or `path` must be provided"
    prefix = prefix or ""
    client = get_client()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if page["KeyCount"] == 0:
            break
        for i in page["Contents"]:
            yield str(Path(i["Key"]).relative_to(prefix))


@parse_path
def download_file(bucket: str, key: str, fpath: str, *, path: str = None) -> None:
    """Download file from s3 to fpath.

    This is a threaded multipart download at a threshold size.
    """
    assert bucket and key
    client = get_client()
    transfer = S3Transfer(client)
    transfer.download_file(bucket, key, fpath)


@parse_path
def upload_file(bucket: str, key: str, fpath: str, *, path: str = None) -> None:
    """Upload file to s3 from fpath.

    This is a threaded multipart upload at a threshold size.
    """
    client = get_client()
    transfer = S3Transfer(client)
    transfer.upload_file(
        fpath, bucket, key, extra_args=dict(ServerSideEncryption="AES256")
    )


@parse_path
def get_object(bucket: str = None, key: str = None, *, path: str = None) -> BinaryIO:
    """Get s3 object.

    The returned object is a file-like object. You can use the `read()`
    method to get the raw content.
    """
    assert bucket and key
    client = get_client()
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"]
