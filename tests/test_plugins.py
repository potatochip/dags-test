import tempfile
from datetime import datetime
from io import BytesIO

import pandas as pd
import pytest
import smart_open
from airflow import DAG
from airflow.models import TaskInstance
from airflow.operators.ingestion import IngestPIIOperator
from airflow.utils.state import State

from utils.aws.s3 import get_client

DEFAULT_DATE = datetime(2020, 4, 1)


def run_operator(operator):
    dag = DAG("test_dag", start_date=DEFAULT_DATE)
    operator.dag = dag
    ti = TaskInstance(task=operator, execution_date=DEFAULT_DATE)
    ti.run(ignore_ti_state=True)
    assert ti.state == State.SUCCESS


class TestIngestion:
    @pytest.mark.parametrize('path, pattern', [
        ('s3://bucket/prefix', r'key.csv'),
        ('bucket/prefix', r'key.csv'),
        ('s3://bucket', r'prefix/key.csv'),
        ('bucket', r'prefix/key.csv'),
    ])
    def test_pii_ingestion(self, path, pattern):
        def callback(df):
            df['callback_column'] = True
            return df

        run_operator(
            IngestPIIOperator(
                task_id='ingest',
                key_pattern=pattern,
                input_path=path,
                output_path='out',
                pii_columns=['msisdn'],
                transform_func=callback
            )
        )
        df = pd.read_csv(smart_open.open('s3://out/prefix/key.csv'))

        assert df.msisdn[0] not in {'123', 123}
        assert df.shape == (1, 4)
        assert df.columns.tolist() == [
            'msisdn', 'pet', 'execution_date', 'callback_column'
        ]

    def test_pii_ingest_empty_file(self):
        run_operator(
            IngestPIIOperator(
                task_id='ingest',
                key_pattern=r'empty.csv',
                input_path='bucket/prefix',
                output_path='out',
                pii_columns=['msisdn'],
                transform_func=lambda df: df
            )
        )
        s3 = get_client()
        response = s3.list_objects(Bucket='bucket', Prefix='prefix/empty.csv')
        assert 'Contents' in response


# todo: use localstack when interacting with local airflow ui

# todo: test actual dag
