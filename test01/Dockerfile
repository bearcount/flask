# ==============================================================================
# SWE-bench Docker Image for: Flask Framework Deployment
# ==============================================================================
# This Dockerfile illustrates the 3-layer image structure used by SWE-bench:
#   1. Base image:       Python + System dependencies (shared across all instances)
#   2. Env image:        Python environment with dependencies (shared by same-env instances)
#   3. Instance image:   Repository cloned at base_commit (unique per instance)
#
# In practice, SWE-bench builds these layers separately and caches them.
# This file combines all three layers for illustration purposes.

# ------ Layer 1: Base Image ------
FROM python:3.12-slim

LABEL maintainer="Flask Team <contact@palletsprojects.com>"
LABEL version="3.2.0.dev"
LABEL description="Flask Web Framework Docker Image"

# Configure apt sources for faster downloads
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        libssl-dev \
        libffi-dev \
        && rm -rf /var/lib/apt/lists/*

# ------ Layer 2: Environment Image ------
# Sets up Python environment "testbed" with the correct Python version and dependencies

COPY ./setup_env.sh /root/
RUN chmod +x /root/setup_env.sh
RUN /bin/bash -c "/root/setup_env.sh"

WORKDIR /work/

# ------ Layer 3: Instance Image ------
# Clones the repository, checks out the base commit, and installs the package

COPY ./instance.json /root/
COPY ./setup_repo.sh /root/
COPY ./verify_instance.sh /root/
RUN chmod +x /root/setup_repo.sh /root/verify_instance.sh
RUN /bin/bash -c "/root/setup_repo.sh"

WORKDIR /work/

# Expose ports
EXPOSE 5000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from flask import Flask; app = Flask(__name__); print('Flask health check passed')"

# Default command - run Flask dev server
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
