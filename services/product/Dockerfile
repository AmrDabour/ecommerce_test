FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create media directory
RUN mkdir -p media staticfiles

# Expose port
EXPOSE 8003

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Run migrations and start server
CMD ["/start.sh"]
