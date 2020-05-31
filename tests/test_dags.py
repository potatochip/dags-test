import logging
from datetime import datetime

import pandas as pd
import pytest
from airflow.models import TaskInstance
from airflow.utils.state import State

from dag.utils.aws.s3 import get_object

DEFAULT_DATE = datetime(2020, 4, 1, 1)


def run_dag_tasks(dag):
    for task in dag.tasks:
        ti = TaskInstance(task=task, execution_date=DEFAULT_DATE)
        ti.run(ignore_ti_state=True)
        assert ti.state == State.SUCCESS


def test_timbrazil_ingest_voice_data(dagbag, populate_s3, mock_anonymizer):
    mock_anonymizer({'5548999027010': '1234567890'})
    # mock s3 data required by the dag
    populate_s3('timbrazil-internal', 'timbrazil-public')
    # run the tasks in the dag
    dag = dagbag.get_dag('timbrazil.anonymize_voice')
    run_dag_tasks(dag)
    # get the dag input and output for comparison
    prefix = 'ocs/ocs_moc/2020/04/01/00'
    raw = pd.read_csv(
        get_object(bucket='timbrazil-internal',
                   key=f'{prefix}/ocs_moc_01_20200401_0001.GZ'),
        compression='gzip',
        header=None,
        skiprows=1,
        delimiter='|')

    anonymized = pd.read_csv(
        get_object(bucket='timbrazil-public',
                   key=f'{prefix}/ocs_moc_01_20200401_0001.csv'))
    # check that files have same structure
    columns = set(anonymized.columns)
    assert 'execution_date' in columns
    assert 'uuid' in columns
    assert anonymized.shape == (2, 456)
    assert raw.shape == (3, 454)

    # check pii encrypted
    pii_columns = [22, 32, 372, 373, 374, 375, 376, 377, 391, 398]
    raw_equivalent = [str(i-1) for i in pii_columns]
    # create dataframe where any values are the same
    equal_pii_columns = anonymized[raw_equivalent].eq(raw[pii_columns])
    # check if any column has any value the same
    assert not any(equal_pii_columns.any())


def test_timbrazil_ingest_large_file(dagbag, populate_s3, mock_anonymizer, monkeypatch):
    mock_anonymizer({'5548999027010': '1234567890'})
    # mock s3 data required by the dag
    populate_s3('timbrazil-internal', 'timbrazil-public')
    # run the tasks in the dag
    dag = dagbag.get_dag('timbrazil.anonymize_voice')
    # set chunksize to 1 to emulate a large file
    monkeypatch.setattr(dag.tasks[0], 'chunksize', 1)
    run_dag_tasks(dag)
    # get the dag input and output for comparison
    prefix = 'ocs/ocs_moc/2020/04/01/00'
    raw = pd.read_csv(
        get_object(bucket='timbrazil-internal',
                   key=f'{prefix}/ocs_moc_01_20200401_0001.GZ'),
        compression='gzip',
        header=None,
        skiprows=1,
        delimiter='|')

    anonymized = pd.read_csv(
        get_object(bucket='timbrazil-public',
                   key=f'{prefix}/ocs_moc_01_20200401_0001.csv'))
    assert anonymized.shape == (2, 456)
    assert raw.shape == (3, 454)


def test_timbrazil_ingest_sms(dagbag, populate_s3, mock_anonymizer):
    mock_anonymizer({'5548999027010': '1234567890'})
    populate_s3('timbrazil-internal', 'timbrazil-public')
    dag = dagbag.get_dag('timbrazil.anonymize_sms')
    run_dag_tasks(dag)
    assert get_object(
        bucket='timbrazil-public',
        key='ocs/ocs_sms/2020/04/01/00/ocs_sms_01_20200401_0001.csv'
    )
