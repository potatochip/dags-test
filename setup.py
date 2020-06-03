"""Installs dag and plugin packages."""
from setuptools import setup, find_packages

setup(
    name='dags',
    version='0.0.0',
    packages=find_packages(),
    install_requires=[
        'boto3>=1.12.0,<2.0.0',
        'pandas<1.0.0,>=0.17.1',  # matches version specced by airflow 1.10.10
        'rfernet~=0.1.3',
    ],
    entry_points={'airflow.plugins': ['ingestion = plugins.ingestion:IngestionPlugin']},
)
