# ==============================================================================
# Flask CSRF Protection Enhancement - Dockerfile
# ==============================================================================
# Multi-stage build for production deployment with CSRF protection
#
# Build command:
#   docker build -t flask-csrf:latest .
#
# Run command:
#   docker run -p 5000:5000 -e SECRET_KEY=your-secret flask-csrf:latest

# ------ Stage 1: Builder ------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ------ Stage 2: Production ------
FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r flaskapp && useradd -r -g flaskapp flaskapp

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/flaskapp/.local
ENV PATH=/home/flaskapp/.local/bin:$PATH

# Copy application code
COPY --chown=flaskapp:flaskapp src/ ./src/
COPY --chown=flaskapp:flaskapp instance.json ./

# Set environment variables
ENV FLASK_APP=src.flask
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# CSRF Protection Configuration
ENV CSRF_ENABLED=true
ENV CSRF_COOKIE_NAME=csrf_token
ENV CSRF_HEADER_NAME=X-CSRF-Token
ENV CSRF_COOKIE_SECURE=true
ENV CSRF_COOKIE_SAMESITE=Lax
ENV CSRF_COOKIE_HTTPONLY=false

# Switch to non-root user
USER flaskapp

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from flask import Flask; print('CSRF Protection Ready')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "src.flask:app"]
