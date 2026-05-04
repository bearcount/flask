# Example application using Flask framework
# This demonstrates how to containerize a Flask application

FROM python:3.12-slim

WORKDIR /app

# Install uv for faster package management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv sync --no-dev

# Copy your application code
COPY app/ ./app/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app \
    FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run with Gunicorn for production
# Adjust workers based on CPU cores (2 * CPU + 1 is a common formula)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "app:create_app()"]
