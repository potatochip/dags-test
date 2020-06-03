"""Operators for ingesting raw carrier files."""
import csv
import gzip
import json
import os
import re
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from typing import Any, Callable, List

import pandas as pd
from airflow.hooks.http_hook import HttpHook
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

from dag.utils.anonymize import Encrypter
from dag.utils.aws import s3
from dag.utils.common import iter_chunks


class PIIOperator(BaseOperator):
    """Ingest raw file and write anonymized version.

    Note: This operator sets the schedule interval internally to @hourly.
    Your dag must do the same.

    This reads a csv and writes an anonymized and optionally transformed
    version of it to our public path. Both the input path and the output
    path are appended with `y/m/d/h` using the hour previous to the execution
    date.

    The execution date is automatically appended as a column in the file.
    """

    template_fields = (
        "key_pattern",
        "input_path",
        "output_path",
        "uuid_read_path",
        "uuid_write_path",
    )
    ui_color = "#ffefeb"
    chunksize = 100000

    @apply_defaults
    def __init__(
        self,
        input_path: str,
        output_path: str,
        *,
        key_pattern: str = None,
        uuid_read_path: str = None,
        uuid_write_path: str = None,
        anonymizer_conn_id: str = None,
        msisdn_column: str = None,
        pii_columns: List[str] = None,
        transform_func: Callable[[pd.DataFrame, str], pd.DataFrame] = None,
        csv_kwargs: dict = None,
        **kwargs: Any,
    ) -> None:
        """Init PIIOperator.

        Args:
            input_path (str): S3 path to raw carrier files
            output_path (str): S3 path where new file will be written
            key_pattern (str, optional): Regex pattern for matching s3 keys.
            uuid_read_path (str, optional): Uses a cache of msisdn to uuid at this
                location. Defaults to None.
            uuid_write_path (str, optional): Writes a cache of msisdn to uuid
                post-anonymization at this location. Defaults to None.
            anonymizer_conn_id (str, optional): Connection id for the carrier's anonymizer service
            msisdn_column (str, optional): Column name that will be used for uuid creation
            pii_columns (str, optional): Column names that contain PII that should be encrypted
            transform_func (Callable[[pd.DataFrame], pd.DataFrame], optional):  A function used to
                transform a dataframe. The function signature should align with the following:
                     `transform(df: DataFrame, msisdn_column: str) -> DataFrame`.
                All columns in the passed dataframe will be of dtype str/object. Defaults to None.
            csv_kwargs (dict, optional): Pandas keyword arguments passed to `pd.read_csv`.
                Defaults to None.
        """
        super().__init__(**kwargs)
        self.input_path = input_path
        self.output_path = output_path
        self.key_pattern = key_pattern
        self.uuid_read_path = uuid_read_path
        self.uuid_write_path = uuid_write_path
        self.msisdn_column = msisdn_column
        self.pii_columns = pii_columns or []
        self.transform_func = transform_func
        self.csv_kwargs = csv_kwargs or {}
        self._encrypter: Encrypter = None
        self._anonymizer_service = HttpHook(http_conn_id=anonymizer_conn_id)
        self._execution_date: datetime = None
        self._msisdn_lookup: dict = {}

    def execute(self, context: Any) -> None:
        """Execute operator task."""
        self._execution_date = context["execution_date"]
        # initialize anonymizer here because sometimes dags on machine with no key
        self._encrypter = Encrypter()

        if self.uuid_read_path:
            self._load_uuids(self.uuid_read_path)

        # pattern is compiled here to allow resolving jinja templating first
        is_target_file = re.compile(self.key_pattern or "", re.I).fullmatch

        path = self._make_path(self.input_path)
        for key in s3.iter_keys(path=path):
            if not self.key_pattern or is_target_file(key):
                self.logger.info("Working on %s", key)
                self._ingest_file(key)

        if self.uuid_write_path:
            self._dump_uuids(self.uuid_write_path)
        self.log.info("Done")

    def _make_path(self, path: str, fname: str = None) -> str:
        """Create timestamped path for s3.

        This reads/writes the previous hour from the execution date.
        """
        timestamp = (self._execution_date - timedelta(hours=1)).strftime("%Y/%m/%d/%H/")
        return os.path.join(path, timestamp, fname or "")

    def _ingest_file(self, fname: str) -> None:
        with TemporaryDirectory() as td:
            local_in = os.path.join(td, "infile.csv")
            local_out = os.path.join(td, "outfile.csv")

            s3_in_path = self._make_path(self.input_path, fname)
            s3.download_file(path=s3_in_path, fpath=local_in)

            try:
                self._iterate_file(local_in, local_out)
            except pd.errors.EmptyDataError:
                self.log.warning("%s is empty", fname)
                return

            fname, _ = os.path.splitext(fname)
            fname += ".csv"
            s3_out_path = self._make_path(self.output_path, fname)
            s3.upload_file(path=s3_out_path, fpath=local_out)
        self.log.info("Wrote %s", s3_out_path)

    def _iterate_file(self, local_in: str, local_out: str) -> None:
        # iterate through the file as a series of dataframes
        reader = pd.read_csv(
            local_in, chunksize=self.chunksize, dtype=str, **self.csv_kwargs
        )

        header = True
        try:
            for df in reader:
                df = self._transform(df)
                df.to_csv(local_out, index=False, header=header, mode="a")
                header = False
        except pd.errors.ParserError as exc:
            # if last frame in reader is just the footer then error will raise
            self.logger.warning(exc)

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.transform_func:
            df = self.transform_func(df, self.msisdn_column)
        if self.msisdn_column:
            df = self._anonymize(df)
        # encrypt pii, including msisdn column, after anonymized uuid created
        df = self._encrypt_pii(df)
        df.loc[:, "execution_date"] = self._execution_date
        return df

    def _anonymize(self, df: pd.DataFrame) -> pd.DataFrame:
        # sometimes non-msisdns are included in an msisdn column
        numeric_msisdns = df[self.msisdn_column].str.isnumeric()
        msisdns = df.loc[numeric_msisdns, self.msisdn_column].copy()

        # check for existence in lookup rather than spending time and money
        # casting to set for each dataframe
        unique_msisdns = set()
        for msisdn in msisdns:
            if msisdn not in self._msisdn_lookup:
                unique_msisdns.add(msisdn)

        # offset the anonymizer timestamp by one hour to correlate with
        # the dag ingesting data from the previou hour.
        timestamp = self._execution_date - timedelta(hours=1)
        for chunk in iter_chunks(list(unique_msisdns), 20000):
            response = self._anonymizer_service.run(
                f"anonymizer/uuids/{timestamp.strftime('%Y-%m-%d')}",
                data=json.dumps(chunk),
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == "200"
            self._msisdn_lookup.update(response.json())

        # cannot map directly over msisdn_lookup because pandas wastes time and
        # memory copying the entire dict into memory again so lambda instead
        df.loc[msisdns.index, "uuid"] = msisdns.map(lambda x: self._msisdn_lookup[x])
        return df

    def _encrypt_pii(self, df: pd.DataFrame) -> pd.DataFrame:
        # add msisdn column as pii in case someone forgot it
        columns = set(self.pii_columns)
        if self.msisdn_column:
            columns.add(self.msisdn_column)

        for column in columns:
            df.loc[:, column] = df[column].map(self._encrypter.encrypt)
        return df

    def _dump_uuids(self, path: str) -> None:
        with TemporaryDirectory() as td:
            local_path = os.path.join(td, "lookup.csv")
            with gzip.open(local_path, "wt") as f:
                writer = csv.writer(f)
                writer.writerows(self._msisdn_lookup.items())

            s3.upload_file(fpath=local_path, path=path)
        self.logger.info("dumped %s", path)
        self._msisdn_lookup = {}

    def _load_uuids(self, path: str) -> None:
        with TemporaryDirectory() as td:
            local_path = os.path.join(td, "lookup.csv")
            s3.download_file(path=path, fpath=local_path)

            with gzip.open(local_path, "rt") as f:
                reader = csv.reader(f)
                for msisdn, uuid in reader:
                    self._msisdn_lookup[msisdn] = uuid
        self.logger.info("loaded %s", path)


class IngestionPlugin(AirflowPlugin):
    """Plugin class for ingestion."""

    name = "ingestion"
    operators = [PIIOperator]
