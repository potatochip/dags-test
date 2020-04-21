#!/usr/bin/env bash
# Load fixtures into localstack for testing the airflow ui
# These are reloaded each time for necessary tests

set -e

# dont bootstrap if test environtment because will create a race condition
# with test fixtures that also populate aws
if [[ $SKIP_BOOTSTRAP -eq 1 ]] ; then exit ; fi

cd /docker-entrypoint-initaws.d/s3
for dir in */
do
    awslocal s3 mb s3://$dir
    awslocal s3 cp --recursive --sse AES256 $dir s3://$dir
done
