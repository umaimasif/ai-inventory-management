#!/bin/sh
# Container entrypoint: bring the schema up to date, then serve.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server on port ${PORT:-7860}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}" --proxy-headers
