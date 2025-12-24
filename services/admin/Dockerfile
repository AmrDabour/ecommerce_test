# Admin Service Dockerfile
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
COPY admin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY admin/app /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]

