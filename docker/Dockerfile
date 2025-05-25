# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy requirements first
COPY fastapi_access_control/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY fastapi_access_control/ .

# Set proper permissions
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 755 /app/alembic && \
    chmod -R 755 /app/alembic/versions && \
    chmod 755 /app/scripts/init_admin_user.py

# Make scripts executable and ensure proper line endings
RUN sed -i 's/\r$//' /app/scripts/init_admin_user.py

# Set PYTHONPATH to include the application directory
ENV PYTHONPATH=/app

# Install development dependencies
RUN pip install -e .

# Switch to non-root user
USER appuser

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 