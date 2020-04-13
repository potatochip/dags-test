"""This file contains global test fixtures.

The location of this file also allows pytest to determine what packages
should be added to path for use within test files.
"""
import logging
import os
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from rfernet import Fernet

THIS_FILE = Path(__file__)
ROOT_DIR = THIS_FILE.parent

ENV = os.environ
# do not set AIRFLOW_HOME in order to avoid littering repo with
# files that airflow creates automatically
ENV['AIRFLOW_CONFIG'] = str(ROOT_DIR.joinpath('airflow.cfg').resolve())
ENV['AIRFLOW__CORE__UNIT_TEST_MODE'] = 'True'
ENV['AIRFLOW__CORE__DAGS_FOLDER'] = str(ROOT_DIR.joinpath('dags').resolve())
ENV['AIRFLOW__CORE__PLUGINS_FOLDER'] = str(ROOT_DIR.joinpath('plugins').resolve())

AIRFLOW_TEST_FERNET_KEY = 'TRSq95QF5Pj9ldN002l0GgLX3ze-d92ZSZAmz3pd4wY='
ENV['FERNET_KEY'] = AIRFLOW_TEST_FERNET_KEY


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
def patch_fernet_key(monkeysession):
    monkeysession.setenv('ANONYMIZER_FERNET_KEY', Fernet.generate_new_key())


@pytest.fixture(scope='session')
def dags_path():
    return ROOT_DIR.joinpath('dags')


@pytest.fixture
def fixture_path():
    def get_path(fname=None):
        path = ROOT_DIR.joinpath('tests', 'fixtures')
        if fname:
            path = path.joinpath(fname)
        return path.resolve()
    return get_path


@pytest.fixture(scope='session')
def dagbag(monkeysession):
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
