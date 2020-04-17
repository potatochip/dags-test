"""This file contains global test fixtures.

The location of this file also allows pytest to determine what packages
should be added to path for use within test files.
"""
import logging
import os
from functools import partialmethod
from pathlib import Path

import boto3
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

# prevent using real account just in case
ENV['AWS_ACCESS_KEY_ID'] = 'testing'
ENV['AWS_SECRET_ACCESS_KEY'] = 'testing'
ENV['AWS_SECURITY_TOKEN'] = 'testing'
ENV['AWS_SESSION_TOKEN'] = 'testing'


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


@pytest.fixture(scope='session', autouse=True)
def mock_aws(monkeysession):
    monkeysession.setattr(boto3.Session, 'client', partialmethod(boto3.Session.client, endpoint_url='http://aws:4566'))
    monkeysession.setattr(boto3.Session, 'resource', partialmethod(boto3.Session.resource, endpoint_url='http://aws:4566'))

    _populate_s3()


def _populate_s3():
    client = boto3.client('s3')
    path = ROOT_DIR.joinpath('tests', 'fixtures', 's3')
    for f in path.rglob('*'):
        bucket, *key = f.relative_to(path).parts
        if f.is_dir():
            client.create_bucket(Bucket=bucket)
            continue
        client.upload_file(str(f.resolve()), bucket, '/'.join(key))
