#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "PostgreSQL is ready!"

echo "Initializing database..."
python -m src.database.scripts.init_db

echo "Starting API server..."
exec python -m uvicorn src.api.ml_api:app --host 0.0.0.0 --port 8000 --reload 