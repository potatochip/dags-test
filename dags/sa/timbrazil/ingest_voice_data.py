"""Ingests raw voice data files from TIM Brazil.

This anonymizes the following fields:

Frequency: Daily incremental extraction.

Inputs:
    S3: timbrazil-internal

Outputs:
    S3: timbrazil-public

Alerts:
    airflow@juvo.com
"""
from datetime import timedelta

from airflow import DAG
from airflow.operators.ingestion import IngestPIIOperator

from dag.settings import timbrazil

# TODO: use pod operator ?

default_args = {
    'owner': 'aaron.mangum',
    'depends_on_past': False,
    'email': ['airflow@juvo.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'sla': timedelta(hours=24),
    'start_date': timbrazil.LAUNCH_DATE
}

dag = DAG('timbrazil.ingest_voice_data',
          default_args=default_args)


def transform_dataframe(df):
    """Transform dataframe."""
    # TODO: placeholder until we know how/if we will transform
    return df


ingest = IngestPIIOperator(
    task_id='ingest',
    key_pattern=r'ocs_mtc_\d+_{{ ds_nodash }}_\d{4}.gz',
    input_path=timbrazil.RAW_CARRIER_BUCKET,
    output_path=timbrazil.ANONYMIZED_CARRIER_BUCKET,
    pii_columns=['PRI_IDENTITY', 'RECIPIENT_NUMBER', 'CallingPartyNumber',
                 'CalledPartyNumber', 'OriginalCalledParty', 'ChargingPartyNumber'],
    transform_func=transform_dataframe,  # NOTE: can be deleted if no transformation
    csv_kwargs=dict(delimiter='|'),
    dag=dag
)
