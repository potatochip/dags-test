"""Install package."""
from setuptools import find_packages, setup

setup(
    name='dag',
    packages=find_packages('dag'),
    python_requires='>=3.8.0',
    install_requires=[],
    extras_require=dict(
        dev=[
            'coverage',
            'flake8',
            'flake8-docstrings',
            'mypy',
            'pytest',
        ],
        test=[
            'pytest',
        ]
    )
)
