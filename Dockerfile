# Production-ready Dockerfile for FastAPI Backend on Render
FROM python:3.12-slim

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    AI_PROVIDER=none \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies needed for native build packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements specification first for optimal layer caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python backend dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source code and root configuration
COPY backend /app/backend
COPY config.py /app/config.py

# Expose default port (Render dynamically sets PORT at runtime)
EXPOSE 8000

# Start FastAPI backend using uvicorn, respecting dynamic $PORT from Render
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
