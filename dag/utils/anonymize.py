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
        """Encrypt a string.

        Args:
            value (str): The string to encrypt

        Returns:
            str: The encrypted string
        """
        # convert to str just in case
        value = str(value)
        return self._fernet.encrypt(value)

    def decrypt(self, value: str) -> str:
        """Decrypt an encrypted string.

        Args:
            value (str): An encrypted string

        Returns:
            str: The string decrypted
        """
        return self._fernet.decrypt(value)
