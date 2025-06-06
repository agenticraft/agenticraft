#!/bin/bash
# Upload to PyPI without using .pypirc

echo "📦 Uploading to TestPyPI without .pypirc"
echo ""
echo "You'll be prompted for your token."
echo "Enter '__token__' as username"
echo "Enter your token (starting with pypi-) as password"
echo ""

# Make sure we're using the venv's twine
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Upload to TestPyPI
python -m twine upload \
    --repository-url https://test.pypi.org/legacy/ \
    --username __token__ \
    dist/*

echo ""
echo "If successful, test with:"
echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agenticraft==0.1.1"
