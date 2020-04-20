"""Operators for ingesting raw carrier files."""
import os
import re
from datetime import datetime
from typing import Any, Callable, List, Optional

import pandas as pd
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

from utils.anonymize import Anonymizer
from utils.aws.s3 import iter_keys, open_s3


def _s3_path(path: str) -> str:
    if not path.startswith('s3://'):
        return 's3://' + path
    return path


class IngestPIIOperator(BaseOperator):
    """Ingest raw file and write anonymized version.

    This reads a csv and writes an anonymized and optionally transformed
    version of it to our public path.

    Note: Beyond matching filenames, they key_pattern is also used for
    writing. So if it is declared with a prefix then that prefix is also
    used when writing the new file to s3.

    The execution date is automatically appended to the file.
    """

    template_fields = ('key_pattern', 'input_path', 'output_path')
    ui_color = '#ffefeb'

    @apply_defaults
    def __init__(self,
                 key_pattern: str,
                 input_path: str,
                 output_path: str,
                 *,
                 pii_columns: List[str],
                 transform_func: Callable[[pd.DataFrame], pd.DataFrame] = None,
                 csv_kwargs: dict = None,
                 **kwargs: Any) -> None:
        """Init IngestPIIOperator.

        Args:
            key_pattern (str): Regex pattern for matching s3 keys.
            input_path (str): Path to raw carrier files
            output_path (str): Path where new file will be written
            pii_columns (str): Column names that contain PII that should be
                encrypted prior to writing.
            transform_func (Callable[[pd.DataFrame], pd.DataFrame], optional):
                A functions used to transform a dataframe. Takes a pandas
                dataframe as a parameter and returns the same. Defaults to None.
            csv_kwargs (dict, optional): Pandas keyword arguments passed to
                `pd.read_csv`. Defaults to None.
        """
        super().__init__(**kwargs)
        self.key_pattern = key_pattern
        self.input_path = _s3_path(input_path)
        self.output_path = _s3_path(output_path)
        self.pii_columns = pii_columns or []
        self.transform_func = transform_func or (lambda df: df)
        self.csv_kwargs = csv_kwargs or {}
        self._anonymizer: Optional[Anonymizer] = None

    def execute(self, context: Any) -> None:
        """Execute operator task."""
        # initialize anonymizer here so can create dags without failure due to no key
        self._anonymizer = Anonymizer()
        is_target_file = re.compile(self.key_pattern, re.I).match
        for key in iter_keys(path=self.input_path):
            if is_target_file(key):
                self._ingest_file(key, context['execution_date'])
        self.log.info("Done")

    def _ingest_file(self, fname: str, execution_date: datetime) -> None:
        input_path = os.path.join(self.input_path, fname)
        output_path = os.path.join(self.output_path, fname)
        # read the s3 file as a series of streamed dataframes
        try:
            reader = pd.read_csv(open_s3(input_path), chunksize=100000, **self.csv_kwargs)
        except pd.errors.EmptyDataError:
            self.log.warning('%s is empty', fname)
            reader = iter([pd.DataFrame()])

        # write the new file as a multipart stream to s3
        with open_s3(output_path, 'w') as f:
            df = next(reader)
            df = self._transform(df, execution_date)
            # write the first chunk with the csv header
            df.to_csv(f, index=False, header=True)
            for df in reader:
                df = self._transform(df, execution_date)
                # every chunk after the first ignore the csv header
                df.to_csv(f, index=False, header=False)
        self.log.info("Wrote %s", output_path)

    def _transform(self, df: pd.DataFrame, execution_date: datetime) -> pd.DataFrame:
        df['execution_date'] = execution_date
        df = self.transform_func(df)
        for column in self.pii_columns:
            df[column] = df[column].map(self._anonymizer.encrypt)
        return df


class IngestionPlugin(AirflowPlugin):
    """Plugin class for ingestion."""

    name = "ingestion"
    operators = [IngestPIIOperator]
