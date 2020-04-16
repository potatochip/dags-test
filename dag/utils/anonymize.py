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
        self._salt = os.getenv('ANONYMIZER_SALT')
        assert self._salt, "Anonymization salt not found in environment"
        self._fernet = Fernet(key)

    def encrypt(self, value: Any) -> bytes:
        """Encrypt a string.

        Args:
            value (Any): The string to encrypt

        Returns:
            bytes: The encrypted string
        """
        value = str(value) + self._salt
        value = value.encode()  # must be bytes
        return self._fernet.encrypt(value)

    def decrypt(self, value: bytes) -> str:
        """Decrypt an encrypted string.

        Args:
            value (bytes): An encrypted string

        Returns:
            str: The decrypted string
        """
        decrypted = self._fernet.decrypt(value)
        decrypted = decrypted.decode()
        return decrypted[:-len(self._salt)]  # remove the salt
