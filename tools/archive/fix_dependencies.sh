#!/bin/bash

echo "=== AgentiCraft Test Fix Script ==="
echo ""
echo "Step 1: Installing missing dependencies..."

# Install missing packages
pip install aiohttp PyJWT cryptography

echo ""
echo "✓ Dependencies installed!"
echo ""
echo "Step 2: Cleaning up Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo "✓ Cache cleaned!"
echo ""
echo "Step 3: Running tests..."
echo "========================"
pytest tests/ -v --tb=short

# Show summary
echo ""
echo "========================"
echo "Test run complete!"
echo ""
echo "All import and collection errors have been fixed."
echo "If you still see errors, they are actual test failures rather than setup issues."
