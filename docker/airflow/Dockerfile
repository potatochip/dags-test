FROM apache/airflow:master-python3.7-ci as builder

WORKDIR /srv

COPY ./requirements/prod.txt .
RUN pip install --trusted-host pypi.python.org -r prod.txt

COPY . .
ENV PYTHONPATH "${PYTHONPATH}:/srv/dag:/srv/settings"

FROM builder as production
ENV AIRFLOW__CORE__FERNET_KEY="eRF9oELwoZLMlJ2BXcCYBlaNUAEV0Ad8jM4POBcGqqc="

FROM builder as test
COPY ./requirements/test.txt .
RUN pip install --trusted-host pypi.python.org -r test.txt
ENTRYPOINT ["/bin/sh", "-c"]
