#!/bin/bash
# Build and publish AgentiCraft to PyPI

set -e  # Exit on error

echo "🚀 AgentiCraft PyPI Publishing Script"
echo "====================================="

# Step 1: Clean previous builds
echo -e "\n📦 Step 1: Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info
echo "✅ Clean complete"

# Step 2: Verify version
echo -e "\n🔍 Step 2: Verifying version..."
VERSION=$(python -c "import agenticraft; print(agenticraft.__version__)")
echo "📌 Version: $VERSION"

# Step 3: Install build tools
echo -e "\n🔧 Step 3: Installing build tools..."
pip install --upgrade build twine

# Step 4: Build the package
echo -e "\n🏗️ Step 4: Building package..."
python -m build
echo "✅ Build complete"

# Step 5: Check the build
echo -e "\n📋 Step 5: Checking build output..."
ls -la dist/
echo ""
twine check dist/*

# Step 6: Test installation
echo -e "\n🧪 Step 6: Testing local installation..."
python -m venv test_install_env
source test_install_env/bin/activate
# Handle both alpha and normalized versions
if [[ $VERSION == *"-alpha"* ]]; then
    NORMALIZED_VERSION=$(echo $VERSION | sed 's/-alpha/a0/')
    pip install dist/agenticraft-${NORMALIZED_VERSION}-py3-none-any.whl
else
    pip install dist/agenticraft-${VERSION}-py3-none-any.whl
fi
python -c "import agenticraft; print(f'✅ AgentiCraft {agenticraft.__version__} installed successfully')"
deactivate
rm -rf test_install_env

echo -e "\n✨ Build verified! Package ready for upload."
echo ""
echo "Next steps:"
echo "1. Upload to TestPyPI first:"
echo "   twine upload --repository testpypi dist/*"
echo ""
echo "2. Test from TestPyPI:"
echo "   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agenticraft==$VERSION"
echo ""
echo "3. Upload to PyPI:"
echo "   twine upload dist/*"
