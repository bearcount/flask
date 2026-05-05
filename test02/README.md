# ==============================================================================
# SWE-bench Flask Testbed - test02
# ==============================================================================
# This directory contains the SWE-bench compatible Docker configuration for 
# the Flask web framework.

## Directory Structure

```
test02/
├── Dockerfile          # Main Dockerfile (3-layer structure)
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
docker build -t flask-swe-bench:test02 .

# Build with custom build args
docker build -t flask-swe-bench:dev --build-arg BASE_COMMIT=HEAD .
```

### Running with Docker Compose

```bash
# Start development container
docker-compose up flask-testbed

# Run in detached mode
docker-compose up -d flask-testbed
```

### Running Directly

```bash
# Run development container
docker run -p 5000:5000 flask-swe-bench:test02

# Run with volume mount
docker run -p 5000:5000 -v $(pwd)/instance.json:/root/instance.json flask-swe-bench:test02
```

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

## Testing

```bash
# Run Flask tests
docker exec flask-swe-bench-test02 pytest

# Run specific tests
docker exec flask-swe-bench-test02 pytest tests/test_templating.py
```

## Benchmark Integration

This testbed is configured for SWE-bench benchmarking:

```json
{
    "instance_id": "flask_framework_testbed",
    "language": "python",
    "task_category": "framework_development"
}
```