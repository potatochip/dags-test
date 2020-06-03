import gzip
import tempfile
from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
import pytest
from airflow import DAG
from airflow.models import TaskInstance
from airflow.operators.ingestion import PIIOperator
from airflow.utils.state import State

from dag.utils.aws.s3 import get_client, get_object

DEFAULT_DATE = datetime(2020, 4, 1, 1)


def run_operator(operator):
    dag = DAG("test_dag", start_date=DEFAULT_DATE)
    operator.dag = dag
    ti = TaskInstance(task=operator, execution_date=DEFAULT_DATE)
    ti.run(ignore_ti_state=True)
    assert ti.state == State.SUCCESS


class TestIngestion:
    @pytest.mark.parametrize(
        "path, out_prefix",
        [
            ("s3://bucket/prefix/", True),
            ("bucket/prefix/", True),
            ("s3://bucket/prefix/", False),
            ("bucket/prefix/", False),
        ],
    )
    def test_pii_ingestion(self, path, out_prefix, populate_s3):
        pattern = r"key.csv"
        populate_s3("bucket/prefix", "out/")

        def callback(df, *a):
            df["callback_column"] = True
            return df

        out_path = "out/prefix" if out_prefix else "out"
        run_operator(
            PIIOperator(
                task_id="ingest",
                input_path=path,
                output_path=out_path,
                key_pattern=pattern,
                pii_columns=["msisdn"],
                transform_func=callback,
            )
        )
        path = f"s3://{out_path}/2020/04/01/00/key.csv"
        df = pd.read_csv(get_object(path=path))

        assert df.msisdn[0] not in {"123", 123}
        assert df.shape == (1, 4)
        assert df.columns.tolist() == [
            "msisdn",
            "pet",
            "callback_column",
            "execution_date",
        ]

    def test_pii_ingest_empty_file(self, populate_s3):
        populate_s3("bucket/", "out/")

        run_operator(
            PIIOperator(
                task_id="ingest",
                input_path="bucket/prefix",
                output_path="out/prefix",
                key_pattern=r"empty.csv",
                pii_columns=[],
            )
        )
        s3 = get_client()
        response = s3.list_objects(
            Bucket="out", Prefix="prefix/2020/04/01/00/empty.csv"
        )
        assert "Contents" not in response

    def test_anonymization(self, mock_anonymizer, populate_s3):
        # explicit test where some non numeric values are interspersed
        # with numeric in an msisdn column
        mock_anonymizer({"8675309": "1234567890"})
        populate_s3("bucket/", "out/")

        run_operator(
            PIIOperator(
                task_id="ingest",
                input_path="bucket/prefix",
                output_path="out/prefix",
                key_pattern="anonymization.csv",
                msisdn_column="msisdn",
            )
        )
        path = "out/prefix/2020/04/01/00/anonymization.csv"
        df = pd.read_csv(get_object(path=path), dtype=str)
        assert df.uuid.to_list() == [
            "1234567890",
            "1234567890",
            np.nan,
            np.nan,
            np.nan,
            "1234567890",
            np.nan,
            "1234567890",
        ]

    def test_anonymization_cache(self, mock_anonymizer, populate_s3):
        mock_anonymizer({"8675309": "1234567890"})
        populate_s3("bucket/", "out/")
        uuid_lookup = "out/msisdn_lookup.csv.gz"

        # test dump
        run_operator(
            PIIOperator(
                task_id="ingest",
                input_path="bucket/prefix",
                output_path="out/prefix",
                uuid_write_path=uuid_lookup,
                key_pattern="anonymization.csv",
                msisdn_column="msisdn",
            )
        )
        with gzip.open(get_object(path=uuid_lookup), "rt") as f:
            content = f.read()
        assert content == "8675309,1234567890\n"

        # test load
        run_operator(
            PIIOperator(
                task_id="ingest",
                input_path="bucket/prefix",
                output_path="out/prefix",
                uuid_read_path=uuid_lookup,
                key_pattern="anonymization.csv",
                msisdn_column="msisdn",
            )
        )
