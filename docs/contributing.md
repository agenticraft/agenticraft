# Contributing to AgentiCraft

Please see our [Contributing Guide](https://github.com/agenticraft/agenticraft/blob/main/CONTRIBUTING.md) on GitHub for detailed information on how to contribute to AgentiCraft.

## Quick Links

- [Code of Conduct](https://github.com/agenticraft/agenticraft/blob/main/CODE_OF_CONDUCT.md)
- [Security Policy](https://github.com/agenticraft/agenticraft/blob/main/SECURITY.md)
- [Issue Tracker](https://github.com/agenticraft/agenticraft/issues)
- [Discussions](https://github.com/agenticraft/agenticraft/discussions)

## Development Setup

```bash
# Clone the repository
git clone https://github.com/agenticraft/agenticraft.git
cd agenticraft

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Build documentation
mkdocs build
```

For full details, please refer to our [Contributing Guide on GitHub](https://github.com/agenticraft/agenticraft/blob/main/CONTRIBUTING.md).
