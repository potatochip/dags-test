# dags

## Table of contents

``` shell
.
├── dags  # dag definitions separated by region/carrier
│   └── sa  # region
│       └── timbrazil  # carrier
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
│   └── timbrazil.py
├── tasks  # package for separating business logic from dag logic
├── tests
│   └── test_something.py
├── utils  # package for common utility functions
├── conftest.py  # global test fixtures
├── README.md
└── setup.cfg
```

## Development

## Fixtures

The directory at tests/fixtures is used to create fixtures that exist for tests and dev airflow.

You can create an empty directory as a bucket in s3. However, git ignores empty directories so you must create some sort of empty file in it to have it added to version control. An empty `.gitignore` works well for this purpose.

### Run Airflow Locally

Use `docker-compose up airflow` to run those airflow components locally. View the UI at `http://localhost:8080`. Run `docker-compose down` when you are finished.

Changes to the codebase should be reflected in the UI and scheduler without needing to restart.

Any changes to requirements files will necessitate runing `docker-compose build airflow`.

### Testing

Test using `./test.sh`. The tests will automatically rerun every time you save a change to the codebase. `ctrl+c` to exit.

You can also run tests directly with `pytest` after installing the root requirements.txt and running `airflow initdb`.
