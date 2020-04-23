"""Installs utils as a namespace package."""
from setuptools import setup, find_packages


setup(
    name='dags',
    version='0.0.0',
    packages=find_packages(include=['utils', 'utils.*']),
    install_requires=[
        'boto3~=1.12.39',
        'pandas~=1.0.3',
        'rfernet~=0.1.3',
        'smart-open~=1.11.1'
    ]
)
