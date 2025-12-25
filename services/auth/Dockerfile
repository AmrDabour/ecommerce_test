# Authentication Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models first (from services/shared)
COPY shared /app/services/shared

# Copy requirements and install dependencies
COPY auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY auth/app /app

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python", "main.py"]
