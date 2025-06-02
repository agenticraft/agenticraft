# Contributing to AgentiCraft

First off, thank you for considering contributing to AgentiCraft! It's people like you that make AgentiCraft such a great tool.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots if possible**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**

### Your First Code Contribution

Unsure where to begin contributing? You can start by looking through these issues:

- [Good first issues](https://github.com/agenticraft/agenticraft/labels/good%20first%20issue)
- [Help wanted issues](https://github.com/agenticraft/agenticraft/labels/help%20wanted)

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/agenticraft.git
cd agenticraft

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
make lint
```

## Style Guide

### Python Style Guide

We use [Black](https://github.com/psf/black) for code formatting and [Ruff](https://github.com/astral-sh/ruff) for linting.

```bash
# Format code
black src tests

# Run linter
ruff check src tests

# Type checking
mypy src
```

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Documentation

- Use [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings
- Update the README.md with details of changes to the interface
- Update the docs/ folder with any new functionality

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agenticraft

# Run specific test file
pytest tests/test_agent.py

# Run with verbose output
pytest -v
```

## Project Structure

```
agenticraft/
├── src/agenticraft/    # Source code
│   ├── core/          # Core functionality
│   ├── tools/         # Built-in tools
│   └── utils/         # Utilities
├── tests/             # Test files
├── docs/              # Documentation
└── examples/          # Example usage
```

## Release Process

1. Update version in `src/agenticraft/__version__.py`
2. Update CHANGELOG.md
3. Create a pull request
4. After merge, create a release on GitHub
5. Package will be automatically published to PyPI

## Questions?

Feel free to ask questions in:
- [Discord](https://discord.gg/agenticraft)
- [GitHub Discussions](https://github.com/agenticraft/agenticraft/discussions)

Thank you for contributing! 🎉
