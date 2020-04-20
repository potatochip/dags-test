from datetime import datetime

import pandas as pd
from airflow.models import TaskInstance
from airflow.utils.state import State

from utils.aws.s3 import open_s3

DEFAULT_DATE = datetime(2020, 4, 1)


def run_dag_tasks(dag):
    for task in dag.tasks:
        ti = TaskInstance(task=task, execution_date=DEFAULT_DATE)
        ti.run(ignore_ti_state=True)
        assert ti.state == State.SUCCESS


def test_timbrazil_ingest_voice_data(dagbag, populate_s3):
    populate_s3('timbrazil-internal', 'timbrazil-public')
    dag = dagbag.get_dag('timbrazil.ingest_voice_data')
    run_dag_tasks(dag)

    raw = pd.read_csv(open_s3('s3://timbrazil-internal/ocs_mtc_01_20200401_0001.gz'), delimiter='|')
    anonymized = pd.read_csv(open_s3('s3://timbrazil-public/ocs_mtc_01_20200401_0001.gz'))

    assert 'execution_date' in anonymized.columns
    no_execution_date = anonymized.drop(columns=['execution_date'])
    assert no_execution_date.shape == raw.shape
    assert no_execution_date.columns.tolist() == raw.columns.tolist()

    pii_columns=['PRI_IDENTITY', 'RECIPIENT_NUMBER', 'CallingPartyNumber',
                 'CalledPartyNumber', 'OriginalCalledParty', 'ChargingPartyNumber']
    # create dataframe where any values are the same
    equal_pii_columns = anonymized[pii_columns].eq(raw[pii_columns])
    # check if any column has any value the same
    assert not any(equal_pii_columns.any())
