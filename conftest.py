"""This file contains global test fixtures.

The location of this file also allows pytest to determine what packages
should be added to path for use within test files.
"""
import logging
import os
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

THIS_FILE = Path(__file__).resolve()
ROOT_DIR = THIS_FILE.parent

ENV = os.environ
# do not set AIRFLOW_HOME in order to avoid littering repo with
# files that airflow creates automatically
ENV['AIRFLOW__CORE__DAGS_FOLDER'] = str(ROOT_DIR.joinpath('dags'))
ENV['AIRFLOW__CORE__PLUGINS_FOLDER'] = str(ROOT_DIR.joinpath('plugins'))

TEST_FERNET_KEY = 'TRSq95QF5Pj9ldN002l0GgLX3ze-d92ZSZAmz3pd4wY='
ENV['FERNET_KEY'] = TEST_FERNET_KEY
ENV['ANONYMIZER_FERNET_KEY'] = TEST_FERNET_KEY
ENV['ANONYMIZER_SALT'] = 'pepper'


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


@pytest.fixture(scope='session')
def this_repo():
    """Get the root directory path for this repo."""
    return ROOT_DIR


@pytest.fixture
def fixture_path():
    """Get the absolute path to a fixture in tests/fixtures."""
    def get_path(fname=None):
        path = ROOT_DIR.joinpath('tests', 'fixtures')
        if fname:
            path = path.joinpath(fname)
        return path
    return get_path


@pytest.fixture(scope='session')
def dagbag():
    """Return a dagbag object from airflow."""
    # import airflow here so envvar changed first
    from airflow.models import DagBag
    return DagBag(include_examples=False)


@pytest.fixture
def disable_airflow_logger():
    """Prevent overly verbose logs from showing when a test fails.

    This is best used when several errors are caught, but are still
    logged like in test_validation.py
    """
    logger = logging.getLogger('airflow.task')
    logger.disabled = True
    yield
    logger.disabled = False
