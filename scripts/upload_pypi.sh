#!/bin/bash
# Upload to PyPI (production) without using .pypirc

echo "📦 Uploading to PyPI (Production)"
echo ""
echo "⚠️  WARNING: This will publish to the real PyPI!"
echo "Make sure you've tested on TestPyPI first."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "You'll be prompted for your token."
echo "Enter '__token__' as username"
echo "Enter your PyPI token (starting with pypi-) as password"
echo ""

# Make sure we're using the venv's twine
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Upload to PyPI
python -m twine upload \
    --username __token__ \
    dist/*

echo ""
echo "If successful, install with:"
echo "pip install agenticraft==0.2.0-alpha"
