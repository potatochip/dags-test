#!/bin/bash

docker-compose run -e SKIP_BOOTSTRAP=1 dev "$@"
docker-compose down -t 1
