"""Installs dag package."""
from setuptools import setup, find_packages


setup(
    name='dags',
    version='0.0.0',
    packages=find_packages(include=['dag', 'dag.*']),
    install_requires=[
        'boto3>=1.12.0,<2.0.0',
        'pandas<1.0.0,>=0.17.1',
        'rfernet~=0.1.3',
    ]
)
