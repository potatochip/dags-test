# dags

## Table of contents

``` shell
.
├── bin
├── dag
│   ├── settings  # package defining constant values for carriers, etc
│   │   ├── __init__.py
│   │   └── timbrazil.py
│   ├── tasks  # package for separating business logic from dag logic
│   ├── utils
│   └── __init__.py
├── dags  # dag definitions separated by region/carrier
│   └── sa  # region
│       └── timbrazil  # carrier
│           └── ingest_voice_data.py
├── k8s  # container definitions for k8s pod operator
│   └── legacy.dockerfile  # used to run legacy python2 code
├── plugins  # airflow plugin directory
├── conftest.py  # global test fixtures
├── README.md
└── setup.cfg
```

## Development

## Fixtures

The directory at tests/fixtures is used to create fixtures that exist for tests and dev airflow.

You can create an empty directory as a bucket in s3. However, git ignores empty directories so you must create some sort of empty file in it to have it added to version control. An empty `.gitignore` works well for this purpose.

### Run Airflow Locally

Use `bin/airflow` to run airflow components locally. View the UI at `http://localhost:8080`. `ctrl+c` to exit.

Changes to the codebase should be reflected in the UI and scheduler without needing to restart.

### Testing

Test using `bin/test`. The tests will automatically rerun every time you save a change to the codebase. `ctrl+c` to exit.

In order to run tests directly with `pytest`, you must install the requirements.txt in root and run `airflow initdb`.
