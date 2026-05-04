# Flask Docker Deployment Guide

This directory contains Docker configurations for the Flask framework.

## Files

- **Dockerfile** - Development environment with hot reload
- **Dockerfile.prod** - Production-optimized multi-stage build
- **docker-compose.yml** - Local development with docker-compose
- **examples/example_app.dockerfile** - Example application Dockerfile
- **.dockerignore** - Docker build exclusion rules

## Quick Start

### Development

```bash
# Build and run development container
docker build -t flask-dev -f Dockerfile .

# Run with port mapping
docker run -p 5000:5000 -v $(pwd)/src:/app/src flask-dev

# Or use docker-compose for easier management
docker-compose up flask-dev
```

### Production

```bash
# Build production image
docker build -t flask-prod -f Dockerfile.prod .

# Run production container
docker run -p 8000:8000 flask-prod
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_APP` | `src.flask` | Application module to import |
| `FLASK_ENV` | `production` | Runtime environment |
| `FLASK_DEBUG` | `0` | Enable debug mode |
| `PYTHONDONTWRITEBYTECODE` | `1` | Prevent .pyc file creation |
| `PYTHONUNBUFFERED` | `1` | Unbuffered output |

## Production Best Practices

1. **Use multi-stage builds** to minimize image size
2. **Run as non-root user** for security
3. **Use Gunicorn** instead of Flask dev server
4. **Configure worker count** based on CPU cores
5. **Set proper health checks**
6. **Use reverse proxy** (nginx/traefik) in production

## Scaling

```bash
# Scale to multiple containers
docker-compose up -d --scale flask-prod=4

# With Gunicorn workers per container
# 2 * CPU cores + 1 is a common formula
```

## Monitoring

Add health check endpoints to your application:

```python
@app.route("/health")
def health():
    return {"status": "healthy"}
```
