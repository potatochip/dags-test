# dags

## Table of contents

```
.
├── dag  # package for dag-related code
│   ├── tasks  # common or carrier-specific task logic
│   ├── utils  # common utilities
├── dags  # dag definitions separated by region/carrier
│   └── sa  # region
│       └── tim_brazil  # carrier
│           └── ingest_voice_data.py
├── docker  # requirements and dockerfile definitions
│   ├── airflow  # the main container for airflow
│   │   ├── requirements
│   │   │   ├── dev.txt
│   │   │   ├── prod.txt
│   │   │   └── test.txt
│   │   └── Dockerfile
│   └── k8s  # container definitions for k8s pod operator
│       └── default.dockerfile
├── plugins  # airflow plugin directory
│   └── myfirstplugin.py
├── settings  # package defining constant values for carriers, etc
│   ├── __init__.py
│   └── tim_brazil.py
├── tests
│   └── test_something.py
├── .dockerignore
├── .gitignore
├── airflow.cfg
├── CODEOWNERS
├── conftest.py
├── Jenkinsfile
├── README.md
├── requirements.txt
└── setup.cfg
```
