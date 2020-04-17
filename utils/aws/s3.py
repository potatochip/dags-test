"""S3-related utility functions."""
import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator

import boto3
import smart_open

_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL')
_CLIENT = None


def get_client() -> boto3.client:
    """Get a client for s3."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = boto3.client('s3', endpoint_url=_ENDPOINT_URL)
    return _CLIENT


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
                **kwargs: dict) -> Any:
        if path:
            path = Path(path.lstrip('s3://'))
            parsed_bucket, *parsed_prefix = path.parts
            parsed_prefix = '/'.join(parsed_prefix) if parsed_prefix else None
        return func(bucket or parsed_bucket, prefix or parsed_prefix, **kwargs)  # type: ignore
    return wrapper



def open_s3(uri, *args, **kwargs) -> smart_open.open:
    """Stream an s3 url for read / write operations.

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
    paginator = client.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
    for page in page_iterator:
        for i in page['Contents']:
            yield i['Key']
