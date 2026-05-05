#!/bin/bash
# ==============================================================================
# Setup Repository Script for Flask Framework
# ==============================================================================
# This script clones the repository, checks out the base commit, 
# and installs the Flask package in development mode.

set -e

echo "=== Setting up Flask repository ==="

# Activate virtual environment
source /opt/testbed/bin/activate

# Set working directory
mkdir -p /work/testbed
cd /work/testbed

# Clone the Flask repository
echo "Cloning Flask repository..."
if [ ! -d ".git" ]; then
    git clone https://github.com/pallets/flask.git .
fi

# Checkout the base commit
BASE_COMMIT="HEAD"
echo "Checking out commit: $BASE_COMMIT"
git checkout $BASE_COMMIT

# Install Flask in development mode
echo "Installing Flask in development mode..."
pip install -e .

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-cov

# Load instance configuration
echo "Loading instance configuration..."
if [ -f /root/instance.json ]; then
    echo "Instance config found at /root/instance.json"
    mkdir -p /work/testbed/instance
    cp /root/instance.json /work/testbed/instance/
else
    echo "Warning: No instance.json found"
fi

# Verify installation
echo "Verifying installation..."
python -c "from flask import Flask; print('Flask version:', Flask.__version__)"

# Deactivate virtual environment
deactivate

echo "=== Repository setup completed ==="