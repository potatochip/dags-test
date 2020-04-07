FROM python:buster

WORKDIR /srv

COPY . ./data-template
RUN pip install ./data-template
