# File: Dockerfile
# Robust Dockerfile for Kryptopedia - works with or without environment variables

FROM python:3.11-slim

# Set default environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p static templates media models routes services dependencies utils pages \
    && chmod -R 755 static templates media

# Create a default .env file if one doesn't exist
# This ensures the app can start even without environment variables
RUN if [ ! -f .env ]; then \
    echo "# Default configuration for Docker" > .env && \
    echo "MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net" >> .env && \
    echo "DB_NAME=kryptopedia" >> .env && \
    echo "JWT_SECRET=default-jwt-secret-please-change-in-production" >> .env && \
    echo "API_DEBUG=false" >> .env && \
    echo "ENVIRONMENT=production" >> .env && \
    echo "STORAGE_TYPE=local" >> .env && \
    echo "MEDIA_FOLDER=/tmp/media" >> .env; \
    fi

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Start command with fallback
# Uses PORT env var if available, defaults to 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1