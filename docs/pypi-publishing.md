# 📦 AgentiCraft PyPI Publishing Guide

This guide walks through publishing AgentiCraft to PyPI.

## Prerequisites

1. **PyPI Accounts**
   - Create account at https://pypi.org
   - Create account at https://test.pypi.org
   - Enable 2FA (recommended)

2. **API Tokens**
   - Go to Account Settings → API tokens
   - Create tokens with "Upload packages" scope
   - Save tokens securely

3. **Configure ~/.pypirc**
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-YOUR-TOKEN-HERE

   [testpypi]
   username = __token__
   password = pypi-YOUR-TEST-TOKEN-HERE
   ```
   
   Then secure it: `chmod 600 ~/.pypirc`

## Publishing Steps

### 1. Pre-publish Check
```bash
cd ~/Desktop/TLV/agenticraft
python scripts/pre_publish_check.py
```

### 2. Build Package
```bash
chmod +x scripts/build_package.sh
./scripts/build_package.sh
```

This will:
- Clean previous builds
- Install build tools
- Build the package
- Verify the build
- Test local installation

### 3. Upload to TestPyPI
```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# You'll see output like:
# Uploading distributions to https://test.pypi.org/legacy/
# Uploading agenticraft-0.1.1-py3-none-any.whl
# Uploading agenticraft-0.1.1.tar.gz
```

### 4. Test from TestPyPI
```bash
# Create a test environment
python -m venv test_pypi_env
source test_pypi_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agenticraft==0.1.1

# Test the installation
python scripts/test_installation.py

# Clean up
deactivate
rm -rf test_pypi_env
```

### 5. Upload to PyPI (Production)
```bash
# Only after TestPyPI verification!
twine upload dist/*

# You'll see:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading agenticraft-0.1.1-py3-none-any.whl
# Uploading agenticraft-0.1.1.tar.gz
```

### 6. Verify on PyPI
1. Visit https://pypi.org/project/agenticraft/
2. Check that all metadata looks correct
3. Test installation: `pip install agenticraft==0.1.1`

## Post-publish Tasks

1. **Update GitHub Release**
   ```bash
   git tag -a v0.1.1 -m "Release v0.1.1: Anthropic/Ollama providers"
   git push origin v0.1.1
   ```

2. **Create GitHub Release**
   - Go to https://github.com/agenticraft/agenticraft/releases
   - Click "Create a new release"
   - Select the v0.1.1 tag
   - Add release notes from CHANGELOG.md

3. **Announce the Release**
   - Update project website
   - Post on social media
   - Notify early users

## Troubleshooting

### "Invalid distribution file"
- Check that version numbers match everywhere
- Ensure no __pycache__ in package
- Rebuild with clean directory

### "Package already exists"
- You can't overwrite PyPI packages
- Bump version number and rebuild
- Delete from TestPyPI (allowed there)

### "Authentication failed"
- Check ~/.pypirc formatting
- Ensure token starts with "pypi-"
- Try with --username __token__ --password pypi-xxx

## Version Management

After publishing 0.1.1:
1. Update version to 0.1.2-dev in:
   - agenticraft/__init__.py
   - pyproject.toml
2. Add new section in CHANGELOG.md
3. Continue development

## Quick Commands Reference

```bash
# Full publish flow
./scripts/build_package.sh
twine upload --repository testpypi dist/*
twine upload dist/*

# Check package on PyPI
pip index versions agenticraft
pip show agenticraft

# Install specific version
pip install agenticraft==0.1.1
pip install agenticraft[all]  # With all extras
pip install agenticraft[openai,anthropic]  # Specific providers
```

## Security Notes

- Never commit .pypirc to git
- Use API tokens, not passwords
- Enable 2FA on PyPI account
- Review package contents before upload
- Test on TestPyPI first

---

Remember: You can't unpublish from PyPI, so test thoroughly on TestPyPI first!
