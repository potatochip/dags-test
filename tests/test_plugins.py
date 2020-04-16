import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from airflow import DAG
from airflow.models import TaskInstance
from airflow.operators.ingestion import IngestPIIOperator
from airflow.utils.state import State

DEFAULT_DATE = datetime(2020, 4, 1)


def run_operator(operator):
    dag = DAG("test_dag", start_date=DEFAULT_DATE)
    operator.dag = dag
    ti = TaskInstance(task=operator, execution_date=DEFAULT_DATE)
    ti.run(ignore_ti_state=True)
    assert ti.state == State.SUCCESS


def csv_file(columns, data):
    df = pd.DataFrame(data, columns=columns)
    obj = BytesIO()
    obj.write(df.to_csv(index=False).encode())
    obj.seek(0)
    return obj


class TestIngestion:
    @pytest.mark.parametrize('path', [
        's3://bucket/prefix',
        's3://bucket',
        'bucket',
    ])
    @pytest.mark.parametrize('as_path', [True, False])
    def test_pii_ingestion(self, path, as_path, s3_stub):
        s3_stub.add_response(
            'list_objects',
            # expected_params={'Bucket': 'bucket', 'Prefix': ''},
            service_response={'Contents': [{'Key': 'cats.csv'}]},
        )
        msisdn = 123
        in_file = csv_file(columns=['msisdn', 'pet'],
                           data=[[msisdn, 'cat']])

        def callback(df):
            df['callback_column'] = True
            return df

        path = Path(path) if as_path else path
        with tempfile.NamedTemporaryFile() as tmp:
            run_operator(
                IngestPIIOperator(
                    task_id='ingest',
                    key_pattern=r'second-prefix/cats.csv',
                    input_path=path,
                    output_path=path,
                    pii_columns=['msisdn'],
                    transform_func=callback
                )
            )
            df = pd.read_csv(tmp.name)

        assert df.msisdn[0] != msisdn
        assert df.shape == (1, 4)
        assert df.columns.tolist() == [
            'msisdn', 'pet', 'execution_date', 'callback_column'
        ]

# todo: test empty pii file
