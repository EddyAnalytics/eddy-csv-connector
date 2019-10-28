#!/bin/sh

if [ "$1" = 'eddy-csv-connector' ]; then
    exec celery worker -A app -l INFO -Q csv-connector
fi

exec "$@"
