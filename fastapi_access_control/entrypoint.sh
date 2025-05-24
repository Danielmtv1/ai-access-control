#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
    sleep 0.1
done
echo "Database ready!"

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 