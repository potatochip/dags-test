ARG AIRFLOW_IMAGE="apache/airflow:1.10.10-python3.7"

FROM ${AIRFLOW_IMAGE} as builder

USER root
RUN mkdir -p /srv && chown -R airflow:airflow /srv
USER airflow
WORKDIR /srv

COPY ./docker/airflow/requirements/prod.txt .
RUN pip install --user --trusted-host pypi.python.org -r prod.txt

ENV PYTHONPATH="${PYTHONPATH}:/srv" \
    AIRFLOW_CONFIG="/srv/airflow.cfg"

# TODO: pass below envvar from k8s secrets
ARG AIRFLOW__CORE__SQL_ALCHEMY_CONN="sqlite:////opt/airflow/airflow.db"
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN ${AIRFLOW__CORE__SQL_ALCHEMY_CONN}

ARG FERNET_KEY
ENV FERNET_KEY ${FERNET_KEY}

ARG PII_FERNET_KEY
ENV PII_FERNET_KEY ${PII_FERNET_KEY}

ARG PII_SALT
ENV PII_SALT ${PII_SALT}


FROM builder as production
COPY --chown=airflow . .


FROM builder as test
COPY ./docker/airflow/requirements/test.txt ./
RUN pip install --user --trusted-host pypi.python.org -r test.txt
COPY ./airflow.cfg .
RUN airflow initdb


FROM test as ci
COPY --chown=airflow . .
ENTRYPOINT []


FROM test as dev
COPY ./docker/airflow/requirements/ .
RUN pip install --user --trusted-host pypi.python.org -r dev.txt
COPY --chown=airflow . .
