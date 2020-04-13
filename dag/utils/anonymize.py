"""Functions for encrypting PII.

We are using a version of fernet with rust bindings since it is much
faster than the native python cryptography implementation.
"""
import os
from typing import Any

from rfernet import Fernet


class Anonymizer:
    """Anonymize PII."""

    def __init__(self) -> None:
        """Init Anonymizer."""
        key = os.getenv('ANONYMIZER_FERNET_KEY')
        assert key, "Anonymization key not found in environment"
        self._fernet = Fernet(key)

    def encrypt(self, value: Any) -> bytes:
        """Encrypt a string.

        Args:
            value (Any): The string to encrypt

        Returns:
            bytes: The encrypted string
        """
        value = str(value).encode()  # must be bytes
        return self._fernet.encrypt(value)

    def decrypt(self, value: bytes) -> bytes:
        """Decrypt an encrypted string.

        Args:
            value (bytes): An encrypted string

        Returns:
            str: The string decrypted
        """
        decrypted = self._fernet.decrypt(value)
        return decrypted.decode()
