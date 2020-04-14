FROM python:3.7-slim-buster as builder

WORKDIR /srv

# Airflow
ARG AIRFLOW_VERSION=1.10.9
ENV AIRFLOW_HOME=/srv

# Define en_US.
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
ENV LC_MESSAGES en_US.UTF-8

RUN set -ex \
    && buildDeps=' \
        freetds-dev \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        git \
    ' \
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
        $buildDeps \
        freetds-bin \
        build-essential \
        default-libmysqlclient-dev \
        apt-utils \
        curl \
        rsync \
        netcat \
        locales \
    && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && pip install -U pip setuptools wheel \
    && pip install pytz \
    && pip install pyOpenSSL \
    && pip install ndg-httpsclient \
    && pip install pyasn1 \
    && pip install apache-airflow[crypto,celery,postgres,hive,jdbc,mysql,ssh]==${AIRFLOW_VERSION} \
    && pip install 'redis==3.2' \
    && apt-get purge --auto-remove -yqq $buildDeps \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

EXPOSE 8080 5555 8793

COPY ./docker/airflow/requirements/prod.txt .
RUN pip install --trusted-host pypi.python.org -r prod.txt

COPY . .
ENV PYTHONPATH="${PYTHONPATH}:/srv"


FROM builder as production

# TODO: pass below from k8s secrets
ENV FERNET_KEY="eRF9oELwoZLMlJ2BXcCYBlaNUAEV0Ad8jM4POBcGqqc=" \
    ANONYMIZER_FERNET_KEY=""

ENTRYPOINT ["/srv/entrypoint.sh"]
CMD ["webserver"]


FROM builder as test

COPY ./docker/airflow/requirements/test.txt ./docker/operators/default/requirements.txt ./
RUN pip install --trusted-host pypi.python.org -r test.txt -r requirements.txt

ENTRYPOINT ["/bin/bash"]
