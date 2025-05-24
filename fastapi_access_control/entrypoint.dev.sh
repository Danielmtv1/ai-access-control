#!/bin/bash

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Wait for database to be ready
print_message "Waiting for database to be ready..." "${YELLOW}"
while ! nc -z db 5432; do
    sleep 0.1
done
print_message "Database ready!" "${GREEN}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_message "Creating virtual environment..." "${YELLOW}"
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if necessary
if [ ! -f "venv/.dependencies_installed" ]; then
    print_message "Installing dependencies..." "${YELLOW}"
    pip install -r requirements.txt
    touch venv/.dependencies_installed
fi

# Run migrations
print_message "Running Alembic migrations..." "${YELLOW}"
alembic upgrade head

# Start application in development mode
print_message "Starting application in development mode..." "${GREEN}"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app 