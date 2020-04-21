#!/bin/bash

docker-compose build dev
docker-compose run -e SKIP_BOOTSTRAP=1 dev "$@"
docker-compose down -t 1
