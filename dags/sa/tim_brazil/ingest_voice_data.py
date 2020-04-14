"""Ingests raw voice data files from TIM Brazil.

Frequency: Daily incremental extraction.

Inputs:
    S3: timbrazil-internal

Outputs:
    S3: timbrazil-public

Alerts:
    airflow@juvo.com
"""
from datetime import timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.ingestion import IngestPIIOperator

from settings import tim_brazil

# TODO
# pod operator
# some sort of means of handling dates or handling multiple dated items
# ingest and anonymize

default_args = {
    'owner': 'aaron.mangum',
    'depends_on_past': False,
    'email': ['airflow@juvo.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'sla': timedelta(hours=24),
    'start_date': tim_brazil.LAUNCH_DATE
}

dag = DAG('tim_brazil.ingest_voice_data',
          default_args=default_args)

PREFIX = 'voice/ocs_file_{{ ds }}.csv'  # TODO: fix me


def transform_dataframe(df):
    """Transform dataframe.

    Mostly revolves around correting msisdn prior to anonymization.
    """
    # cast msisdn columns to str if failed to cast on initial read
    df['MSISDN_A'] = df.MSISDN_A.astype(str)
    df['MSISDN_B'] = df.MSISDN_B.astype(str)
    # filter rows where not a valid msisdn
    # brazil mobile numbers are 11 digits, landlines are 10
    df = df[df.MSISDN_A.str.len() >= 10]
    df = df[df.MSISDN_B.str.len() >= 10]
    # prepend msisdn with country code
    df['MSISDN_A'] = '55' + df.MSISDN_A
    df['MSISDN_B'] = '55' + df.MSISDN_B

    df['landline_called'] = df.MSISDN_B.str.len() == 10
    return df


ingest = IngestPIIOperator(
    task_id='ingest',
    input_path=Path('s3://', tim_brazil.RAW_CARRIER_BUCKET, PREFIX),
    output_path=Path('s3://', tim_brazil.ANONYMIZED_CARRIER_BUCKET, PREFIX),
    pii_columns=['MSISDN_A', 'MSISDN_B'],
    transform_func=transform_dataframe,
    csv_kwargs=dict(delimiter=';')
)
