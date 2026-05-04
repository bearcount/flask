# ==============================================================================
# SWE-bench Flask Testbed
# ==============================================================================
# This directory contains the SWE-bench compatible Docker configuration for 
# the Flask web framework.

## Directory Structure

```
test01/
├── Dockerfile          # Main Dockerfile (3-layer structure)
├── Dockerfile.prod     # Production-optimized Dockerfile
├── docker-compose.yml  # Docker Compose configuration
├── setup_env.sh        # Environment setup script
├── setup_repo.sh       # Repository setup script
├── instance.json       # Instance configuration
└── README.md           # This file
```

## Usage

### Building the Image

```bash
# Build development image
docker build -t flask-swe-bench:latest .

# Build with custom build args
docker build -t flask-swe-bench:dev --build-arg BASE_COMMIT=HEAD .
```

### Running with Docker Compose

```bash
# Start development container
docker-compose up flask-testbed

# Start production container
docker-compose up flask-prod

# Run in detached mode
docker-compose up -d flask-testbed
```

### Running Directly

```bash
# Run development container
docker run -p 5000:5000 flask-swe-bench

# Run with volume mount
docker run -p 5000:5000 -v $(pwd)/instance.json:/root/instance.json flask-swe-bench
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | development | Runtime environment |
| FLASK_APP | src.flask | Application module |
| PYTHONDONTWRITEBYTECODE | 1 | Prevent .pyc files |
| PYTHONUNBUFFERED | 1 | Unbuffered output |

## Image Layers

The Dockerfile follows the SWE-bench 3-layer structure:

### Layer 1: Base Image
- Python 3.12 slim
- System dependencies (git, build-essential)
- Apt sources configured for faster downloads

### Layer 2: Environment Image
- Python virtual environment at /opt/testbed
- Flask and all dependencies installed
- Development tools (pytest, sphinx)

### Layer 3: Instance Image
- Repository cloned at base commit
- Flask installed in development mode
- Instance configuration loaded

## Verification Scripts

### Quick Test
```bash
# Build the container
docker build -t flask-swe-bench .

# Run the container
docker run -it flask-swe-bench /bin/bash

# From within the container, run quick test
/work/testbed/quick_test.sh
```

### Full Instance Verification
```bash
# Build and start container
docker build -t flask-swe-bench .
docker run -it flask-swe-bench /bin/bash

# From within the container
cd /work/testbed
./verify_instance.sh
```

### Verification Workflow
1. Loads instance.json configuration
2. Applies code.patch and test.patch
3. Runs PASS_TO_PASS tests
4. Generates verification report at /work/testbed/logs/
5. Exits 0 on success, 1 on failure

## Testing

```bash
# Run Flask tests
docker exec flask-swe-bench pytest

# Run specific tests
docker exec flask-swe-bench pytest tests/test_templating.py
```

## Production Deployment

```bash
# Build production image
docker build -t flask-swe-bench:prod -f Dockerfile.prod .

# Run production container
docker run -p 8000:8000 flask-swe-bench:prod
```

## Benchmark Integration

This testbed is configured for SWE-bench benchmarking:

```json
{
    "SWE_BENCH_CONFIG": {
        "benchmark_name": "flask-framework",
        "testbed_version": "3.2.0.dev",
        "instance_id": "test01"
    }
}
```
