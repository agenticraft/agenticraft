#!/bin/bash
# scripts/test.sh

echo "🧪 Running AgentiCraft Tests..."

# Run tests with coverage
pytest -v --cov=agenticraft --cov-report=term-missing --cov-report=html

# Run type checking
echo "🔍 Running type checks..."
mypy agenticraft/

# Run linting
echo "✨ Running linting..."
ruff check agenticraft/ tests/
black --check agenticraft/ tests/

echo "✅ All checks complete!"
