"""This file contains global test fixtures.

The location of this file also allows pytest to determine what packages
should be added to path for use within test files.
"""
import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(scope='session')
def monkeysession():
    """Patch to use monkeypatch with session-scoped fixtures.

    Use `monkeypatch` instead for function scoped fixtures.
    """
    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope='module')
def monkeymodule():
    """Patch to use monkeypatch with module-scoped fixtures.

    Use `monkeypatch` instead for function scoped fixtures.
    """
    m = MonkeyPatch()
    yield m
    m.undo()
