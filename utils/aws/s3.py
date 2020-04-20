"""S3-related utility functions."""
import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator

import boto3
import smart_open

_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL')  # largely used for mocking aws
_S3 = None


def get_s3() -> boto3.resource:
    """Get the s3 resource."""
    global _S3
    if _S3 is None:
        _S3 = boto3.resource('s3', endpoint_url=_ENDPOINT_URL)
    return _S3


def get_client() -> boto3.client:
    """Get a client for s3."""
    s3 = get_s3()
    return s3.meta.client


def parse_path(func: Callable[[str, str], Any]) -> Callable:
    """Decorate function to accept path argument.

    Parse an optionally provided path and pass bucket/prefix arguments to
    the underlying function.
    """
    @wraps(func)
    def wrapper(bucket: str = None,
                prefix: str = None,
                *,
                path: str = None,
                **kwargs: Any) -> Any:
        if path:
            path = path.lstrip('s3://')
            parsed_bucket, *parsed_prefix = path.split(os.sep)
            parsed_prefix = '/'.join(parsed_prefix) if parsed_prefix else None
        return func(bucket or parsed_bucket, prefix or parsed_prefix, **kwargs)  # type: ignore
    return wrapper


def open_s3(uri: str, *args: Any, **kwargs: Any) -> smart_open.open:
    """Stream an s3 key for read / write operations.

    This is a wrapper around smart_open.open which allows us to fine-tune
    access control for testing.
    """
    transport_params = {
        'resource_kwargs': {
            'endpoint_url': _ENDPOINT_URL,
        }
    }
    return smart_open.open(uri, transport_params=transport_params, *args, **kwargs)


@parse_path
def iter_keys(bucket: str = None, prefix: str = None) -> Generator[str, None, None]:
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
    prefix = prefix or ''
    client = get_client()
    paginator = client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
    for page in page_iterator:
        for i in page['Contents']:
            yield str(Path(i['Key']).relative_to(prefix))
