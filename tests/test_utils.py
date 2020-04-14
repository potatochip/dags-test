import pytest

from dag.utils.anonymize import Anonymizer


@pytest.mark.parametrize('value', [
    '123',
    b'123',
    123,
    True,
    ''
])
def test_anonymizer(value):
    anonymizer = Anonymizer()
    encrypted = anonymizer.encrypt(value)
    decrypted = anonymizer.decrypt(encrypted)
    assert str(value) == decrypted
