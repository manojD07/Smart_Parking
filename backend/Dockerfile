# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Build arguments for versioning
ARG VERSION=1.0.0
ARG COMMIT_ID=unknown
ARG BUILD_DATE
ARG REGISTRY=

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_VERSION=${VERSION} \
    APP_COMMIT_ID=${COMMIT_ID} \
    APP_BUILD_DATE=${BUILD_DATE}

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Add build information
RUN echo "Smart Parking Backend" > /app/build_info.txt && \
    echo "Version: ${VERSION}" >> /app/build_info.txt && \
    echo "Commit: ${COMMIT_ID}" >> /app/build_info.txt && \
    echo "Build Date: ${BUILD_DATE}" >> /app/build_info.txt && \
    echo "Registry: ${REGISTRY}" >> /app/build_info.txt

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
