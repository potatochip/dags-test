"""Tasks for ingesting raw carrier files."""
from typing import Any, Callable, List

import pandas as pd
from smart_open import open

from dag.utils.anonymize import Anonymizer


def ingest_pii_file(input_path: str,
                    output_path: str,
                    pii_columns: List[str],
                    *,
                    transform_func: Callable[[pd.DataFrame], pd.DataFrame] = None,
                    csv_kwargs: dict = None,
                    **context: Any) -> None:
    """Ingest raw file and write anonymized version.

    This reads a csv and writes an anonymized and optionally transformed
    version of it to our public path.

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
    def transform(df: pd.DataFrame) -> pd.DataFrame:
        df['execution_date'] = context['execution_date']
        df = transform_func(df)
        for column in pii_columns:
            df[column] = df[column].map(anonymizer.encrypt)
        return df

    pii_columns = pii_columns or []
    transform_func = transform_func or (lambda df: df)
    csv_kwargs = csv_kwargs or {}
    anonymizer = Anonymizer()

    # read the s3 file as a series of streamed dataframes
    reader = pd.read_csv(open(input_path), chunksize=100000, **csv_kwargs)

    # write the new file as a multipart stream to s3
    with open(output_path, 'w') as f:
        df = next(reader)
        df = transform(df)
        # write the first chunk with the csv header
        df.to_csv(f, index=False, header=True)
        for df in reader:
            df = transform(df)
            # every chunk after the first ignore the csv header
            df.to_csv(f, index=False, header=False)
