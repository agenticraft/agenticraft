#!/bin/bash

# Install development dependencies for AgentiCraft

echo "Setting up AgentiCraft development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install package in development mode
echo "Installing AgentiCraft in development mode..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo "Development environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
