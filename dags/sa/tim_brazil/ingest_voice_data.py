from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from dag.tasks.ingest import ingest_pii_file
from setting import tim_brazil
