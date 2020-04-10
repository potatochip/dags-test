"""Functions for encrypting PII.

We are using a version of fernet with rust bindings since it is much
faster than the native python cryptography implementation.
"""
import os

from rfernet import Fernet


class Anonymizer:
    """Anonymize PII."""

    def __init__(self) -> None:
        """Init Anonymizer."""
        key = os.getenv('FERNET_KEY')
        assert key, "Anonymization key not found in environment"
        self._fernet = Fernet(key)

    def encrypt(self, value: str) -> str:
        """Encrypt a value."""
        # convert to str just in case
        value = str(value)
        return self._fernet.encrypt(value)

    def decrypt(self, value: str) -> str:
        """Decrypt a value."""
        return self._fernet.decrypt(value)
