"""This file contains global test fixtures.

The location of this file also allows pytest to determine what packages
should be added to path for use within test files.
"""
import logging
import os
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from utils.aws.s3 import get_s3

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

_S3_BUCKETS = set()


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


@pytest.fixture
def populate_s3():
    """Populate s3 files in the mocked aws.

    This should be run every time a specific fixture is necessary
    to ensure that no artifacts remain from previous tests.
    """
    def populate(*paths):
        """Populate s3 files for passed paths.

        If no paths are passed then populates all files.
        """
        included_paths = [Path(i) for i in paths]
        path = ROOT_DIR.joinpath('tests', 'fixtures', 's3')
        s3 = get_s3()
        emptied_buckets = set()
        for f in path.rglob('*'):
            relative_path = f.relative_to(path)
            if included_paths and not any(
                p in relative_path.parents or p == relative_path
                for p in included_paths
            ):
                continue
            bucket, *key = relative_path.parts
            bucket = s3.Bucket(bucket)
            if bucket not in _S3_BUCKETS:
                bucket.create()
                _S3_BUCKETS.add(bucket)
            if bucket not in emptied_buckets:
                bucket.objects.delete()
                emptied_buckets.add(bucket)
            if f.is_file():
                bucket.upload_file(
                    Filename=str(f.resolve()),
                    Key='/'.join(key),
                    ExtraArgs={'ServerSideEncryption': 'AES256'}
                )
    return populate
