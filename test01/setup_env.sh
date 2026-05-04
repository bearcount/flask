#!/bin/bash
# ==============================================================================
# Setup Environment Script for Flask Framework
# ==============================================================================
# This script sets up the Python environment "testbed" with the correct 
# Python version and dependencies for the Flask project.

set -e

echo "=== Setting up Flask environment ==="

# Set environment variables
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export FLASK_ENV=development
export FLASK_APP=src.flask

# Create virtual environment
echo "Creating virtual environment..."
python -m venv /opt/testbed

# Activate virtual environment
source /opt/testbed/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install uv for faster package management
echo "Installing uv..."
pip install uv

# Install Flask dependencies
echo "Installing Flask and dependencies..."
uv pip install \
    flask \
    werkzeug \
    jinja2 \
    click \
    itsdangerous \
    blinker \
    markupsafe

# Install development dependencies
echo "Installing development dependencies..."
uv pip install \
    pytest \
    pytest-cov \
    python-dotenv \
    sphinx \
    sphinx-rtd-theme

# Deactivate virtual environment
deactivate

echo "=== Environment setup completed ==="
