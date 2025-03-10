#!/bin/bash

export PYTHONPATH=$(pwd)

poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 &
poetry run celery -A app.task_scheduler.task worker --loglevel=info

wait