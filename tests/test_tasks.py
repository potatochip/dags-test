import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from rfernet import Fernet

from dag.tasks.ingest import ingest_pii_file


@pytest.fixture
def csv_file():
    """Return a file-like object representation of a csv file."""
    def get_csv(columns, data):
        df = pd.DataFrame(data, columns=columns)
        obj = BytesIO()
        obj.write(df.to_csv(index=False).encode())
        obj.seek(0)
        return obj
    return get_csv


@pytest.mark.usefixtures('patch_fernet_key')
def test_raw_ingestion(fixture_path, csv_file):
    def callback(df):
        df['callback_column'] = True
        return df

    msisdn = 123
    in_file = csv_file(columns=['msisdn', 'pet'],
                       data=[[msisdn, 'cat']])

    with tempfile.NamedTemporaryFile() as tmp:
        ingest_pii_file(input_path=in_file,
                        output_path=tmp.name,
                        pii_columns=['msisdn'],
                        transform_func=callback,
                        execution_date=datetime(2020, 4, 1))
        df = pd.read_csv(tmp.name)
    assert df.msisdn[0] != msisdn
    assert df.shape == (1, 4)
    assert df.columns.tolist() == [
        'msisdn', 'pet', 'execution_date', 'callback_column'
    ]
