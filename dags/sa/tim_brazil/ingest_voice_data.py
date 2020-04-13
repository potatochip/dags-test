from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from dag.tasks.ingest import ingest_pii_file
from settings import tim_brazil


# pod operator
# some sort of means of handling dates or handling multiple dated items
# ingest and anonymize
