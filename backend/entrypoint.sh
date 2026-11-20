#!/usr/bin/env sh
set -eu

cd /app/backend

# Apply pending database migrations before serving.
alembic upgrade head

# Start the FastAPI application.
exec uvicorn main:app --host 0.0.0.0 --port 8000