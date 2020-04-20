import tempfile
from datetime import datetime
from io import BytesIO

import pandas as pd
import pytest
from airflow import DAG
from airflow.models import TaskInstance
from airflow.operators.ingestion import IngestPIIOperator
from airflow.utils.state import State

from utils.aws.s3 import get_client, open_s3

DEFAULT_DATE = datetime(2020, 4, 1)


def run_operator(operator):
    dag = DAG("test_dag", start_date=DEFAULT_DATE)
    operator.dag = dag
    ti = TaskInstance(task=operator, execution_date=DEFAULT_DATE)
    ti.run(ignore_ti_state=True)
    assert ti.state == State.SUCCESS


class TestIngestion:
    @pytest.mark.parametrize('path, pattern, expected_out', [
        ('s3://bucket/prefix/', r'key.csv', 's3://out/key.csv'),
        ('bucket/prefix/', r'key.csv', 's3://out/key.csv'),
        ('s3://bucket/', r'prefix/key.csv', 's3://out/prefix/key.csv'),
        ('bucket/', r'prefix/key.csv', 's3://out/prefix/key.csv'),
    ])
    def test_pii_ingestion(self, path, pattern, expected_out, populate_s3):
        populate_s3('bucket/prefix/key.csv', 'out/')

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
        s3 = get_client()
        df = pd.read_csv(open_s3(expected_out))

        assert df.msisdn[0] not in {'123', 123}
        assert df.shape == (1, 4)
        assert df.columns.tolist() == [
            'msisdn', 'pet', 'execution_date', 'callback_column'
        ]

    def test_pii_ingest_empty_file(self, populate_s3):
        populate_s3('bucket/empty.csv', 'out/')

        run_operator(
            IngestPIIOperator(
                task_id='ingest',
                key_pattern=r'empty.csv',
                input_path='bucket',
                output_path='out',
                pii_columns=[]
            )
        )
        s3 = get_client()
        response = s3.list_objects(Bucket='out', Prefix='empty.csv')
        assert 'Contents' in response
