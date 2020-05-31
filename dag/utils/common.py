"""General utility functions."""
from itertools import islice
from typing import Iterable, Iterator, Sequence, Union


def iter_chunks(sequence: Union[Iterable, Sequence], n: int) -> Iterator:
    """Yield n-size chunks from the sequence."""
    if isinstance(sequence, Iterator):
        return _dispatch_chunk_iterable(sequence, n)
    # this will be faster if not passed an iterable
    assert isinstance(sequence, Sequence)
    return _dispatch_chunk_sequence(sequence, n)


def _dispatch_chunk_iterable(sequence: Iterable, n: int) -> Iterator:
    while True:
        chunk = tuple(islice(sequence, n))
        if not chunk:
            break
        yield chunk


def _dispatch_chunk_sequence(sequence: Sequence, n: int) -> Iterator:
    for i in range(0, len(sequence), n):
        yield sequence[i:i + n]
