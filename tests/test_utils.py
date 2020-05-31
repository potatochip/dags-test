import pytest

from dag.utils.anonymize import Encrypter


@pytest.mark.parametrize('value', [
    '123',
    b'123',
    123,
    True,
    ''
])
def test_anonymizer(value):
    e = Encrypter()
    encrypted = e.encrypt(value)
    decrypted = e.decrypt(encrypted)
    assert str(value) == decrypted
