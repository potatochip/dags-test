"""Operators for ingesting raw carrier files."""
from datetime import datetime
from typing import Any, Callable, List, Optional

import pandas as pd
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from smart_open import open

from dag.utils.anonymize import Anonymizer


class IngestPIIOperator(BaseOperator):
    """Ingest raw file and write anonymized version.

    This reads a csv and writes an anonymized and optionally transformed
    version of it to our public path.

    The execution date is automatically appended to the file.
    """

    template_fields = ('input_path', 'output_path')
    ui_color = '#ffefeb'

    @apply_defaults
    def __init__(self,
                 input_path: str,
                 output_path: str,
                 pii_columns: List[str],
                 *,
                 transform_func: Callable[[pd.DataFrame], pd.DataFrame] = None,
                 csv_kwargs: dict = None,
                 **kwargs: Any) -> None:
        """Init IngestPIIOperator.

        Args:
            input_path (str): Path to raw carrier file
            output_path (str): Path where new file should be written
            pii_columns (str): Column names that contain PII that should be
                encrypted prior to writing.
            transform_func (Callable[[pd.DataFrame], pd.DataFrame], optional):
                A functions used to transform a dataframe. Takes a pandas
                dataframe as a parameter and returns the same. Defaults to None.
            csv_kwargs (dict, optional): Pandas keyword arguments passed to
                `pd.read_csv`. Defaults to None.
        """
        super().__init__(**kwargs)
        self.input_path = input_path
        self.output_path = output_path
        self.pii_columns = pii_columns or []
        self.transform_func = transform_func or (lambda df: df)
        self.csv_kwargs = csv_kwargs or {}
        self._anonymizer: Optional[Anonymizer] = None

    def execute(self, context: Any) -> None:
        """Execute operator task."""
        # initialize here to allow dag creation without failure due to no key
        self._anonymizer = Anonymizer()

        # read the s3 file as a series of streamed dataframes
        reader = pd.read_csv(open(self.input_path), chunksize=100000, **self.csv_kwargs)

        # write the new file as a multipart stream to s3
        with open(self.output_path, 'w') as f:
            df = next(reader)
            df = self._transform(df, context['execution_date'])
            # write the first chunk with the csv header
            df.to_csv(f, index=False, header=True)
            for df in reader:
                df = self._transform(df, context['execution_date'])
                # every chunk after the first ignore the csv header
                df.to_csv(f, index=False, header=False)
        self.log.info("Done")

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
