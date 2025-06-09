# Example Tests Usage

## Overview

There are two ways to test the examples:

### 1. Standalone Script (Original)
The file `tests/examples/test_examples.py` is a standalone script that checks if reasoning examples are properly structured.

**Usage:**
```bash
# Run directly as a script
python tests/examples/test_examples.py
```

This will:
- Check if example files exist
- Verify they have a `main()` function
- Display results in a nice table format using Rich
- Check for API keys in environment

### 2. Pytest Test
The file `tests/examples/test_examples_pytest.py` is a proper pytest test that can be run as part of the test suite.

**Usage:**
```bash
# Run with pytest
pytest tests/examples/test_examples_pytest.py -v
```

This will:
- Run as part of the test suite
- Check example files in `examples/reasoning/`
- Skip tests if files are missing (rather than fail)

## Note

The original `test_examples.py` was never meant to be run with pytest - it's a utility script that happens to be in the tests directory. The naming convention (`test_*.py`) made pytest try to collect it as a test, which caused the error.

Both approaches are valid:
- Use the script for interactive checking with nice output
- Use the pytest version for CI/CD integration
