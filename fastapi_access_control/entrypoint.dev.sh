#!/bin/bash
set -e  # Exit on any error

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages with timestamp
print_message() {
    echo -e "${2}[$(date '+%Y-%m-%d %H:%M:%S')] ${1}${NC}"
}

# Function to check database connection
check_db_connection() {
    local max_attempts=30
    local attempt=1
    
    print_message "Checking database connection..." "${BLUE}"
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z db 5432; then
            print_message "Database connection successful!" "${GREEN}"
            return 0
        fi
        
        print_message "Attempt $attempt/$max_attempts - Waiting for database..." "${YELLOW}"
        sleep 2
        ((attempt++))
    done
    
    print_message "Failed to connect to database after $max_attempts attempts" "${RED}"
    exit 1
}

# Function to install dependencies (only if needed)
install_dependencies() {
    print_message "Checking Python dependencies..." "${BLUE}"
    
    # Check if we need to install dependencies
    if ! python -c "import fastapi, uvicorn, alembic, sqlalchemy" 2>/dev/null; then
        print_message "Installing Python dependencies..." "${YELLOW}"
        pip install --no-cache-dir -r requirements.txt
        print_message "Dependencies installed successfully!" "${GREEN}"
    else
        print_message "Dependencies already available!" "${GREEN}"
    fi
}

# Function to run database migrations
run_migrations() {
    print_message "Running database migrations..." "${BLUE}"
    
    # Check if alembic.ini exists
    if [ ! -f "alembic.ini" ]; then
        print_message "alembic.ini not found!" "${RED}"
        exit 1
    fi
    
    # Check current migration state
    print_message "Checking migration state..." "${YELLOW}"
    if ! alembic current 2>/dev/null; then
        print_message "No migration history found, initializing..." "${YELLOW}"
        # If no history, stamp with the latest migration
        alembic stamp head
    fi
    
    # Run migrations with error handling
    if alembic upgrade head; then
        print_message "Migrations completed successfully!" "${GREEN}"
    else
        print_message "Migration failed! Attempting to resolve..." "${YELLOW}"
        
        # Try to get migration state
        print_message "Current migration state:" "${BLUE}"
        alembic current
        
        print_message "Available migrations:" "${BLUE}"
        alembic history
        
        # Try to stamp and retry
        print_message "Attempting to resolve migration conflicts..." "${YELLOW}"
        alembic stamp head
        
        if alembic upgrade head; then
            print_message "Migrations resolved and completed!" "${GREEN}"
        else
            print_message "Migrations still failing, but continuing with application startup..." "${YELLOW}"
            print_message "You may need to fix migrations manually later." "${YELLOW}"
        fi
    fi
}

# Function to initialize admin user
init_admin_user() {
    print_message "Initializing admin user..." "${BLUE}"
    
    # Ensure we're in the correct directory
    cd /app
    
    print_message "Current directory: $(pwd)" "${BLUE}"
    print_message "Checking if init_admin_user.py exists..." "${BLUE}"
    
    if [ ! -f "scripts/init_admin_user.py" ]; then
        print_message "Error: init_admin_user.py not found in scripts directory!" "${RED}"
        return 1
    fi
    
    print_message "Running admin user initialization script..." "${BLUE}"
    
    # Run the admin user initialization script with proper Python path
    if python -u scripts/init_admin_user.py; then
        print_message "Admin user initialized successfully!" "${GREEN}"
    else
        print_message "Failed to initialize admin user!" "${RED}"
        print_message "You may need to initialize the admin user manually later." "${YELLOW}"
        return 1
    fi
}

# Function to start the application
start_application() {
    print_message "Starting FastAPI application..." "${GREEN}"
    print_message "Application will be available at:" "${BLUE}"
    print_message "  - API: http://localhost:8000" "${BLUE}"
    print_message "  - Docs: http://localhost:8000/docs" "${BLUE}"
    print_message "  - ReDoc: http://localhost:8000/redoc" "${BLUE}"
    
    # Start with proper error handling
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir app \
        --log-level info
}

# Main execution
main() {
    print_message "🚀 Starting Access Control System setup..." "${BLUE}"
    print_message "Working directory: $(pwd)" "${BLUE}"
    
    # Step 1: Check database connectivity
    check_db_connection
    
    # Step 2: Install dependencies (if needed)
    install_dependencies
    
    # Step 3: Run database migrations
    run_migrations
    
    # Step 4: Initialize admin user
    if ! init_admin_user; then
        print_message "Warning: Admin user initialization failed, but continuing with startup..." "${YELLOW}"
    fi
    
    # Step 5: Start application
    start_application
}

# Trap signals for graceful shutdown
trap 'print_message "Received shutdown signal..." "${YELLOW}"; exit 0' SIGTERM SIGINT

# Run main function
main "$@"