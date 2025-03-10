#!/bin/bash

export PYTHONPATH=$(pwd)

gunicorn -w 3 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:7860 &
celery -A app.task_scheduler.task worker --loglevel=info

wait