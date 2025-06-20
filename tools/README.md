# AgentiCraft Development Tools

This directory contains development, diagnostic, and maintenance tools for the AgentiCraft project. These tools were previously scattered in the root directory and have been organized here for better project structure.

## Directory Structure

```
tools/
├── diagnostics/     # Diagnostic and verification scripts
├── scripts/         # Execution and test runner scripts
├── archive/         # Old/deprecated scripts for reference
└── development/     # Active development and analysis tools
```

## Usage Guidelines

### For Developers

1. **Running Diagnostics**: Use scripts in `diagnostics/` to check project health
2. **Running Tests**: Use scripts in `scripts/` to execute various test suites
3. **Development Tools**: Use `development/` tools for analysis and refactoring

### Important Notes

- Scripts in `archive/` are deprecated and kept for reference only
- Always run scripts from the project root directory
- Some scripts may have dependencies - check script headers

## Quick Reference

### Common Diagnostic Commands
```bash
# Check all imports
python tools/diagnostics/check_all_imports.py

# Verify import fixes
python tools/diagnostics/verify_all_imports.py

# Check test status
python tools/diagnostics/check_test_status.py
```

### Common Test Runners
```bash
# Run all tests
bash tools/scripts/run_tests.sh

# Run security tests
python tools/scripts/run_security_tests_full.py

# Run specific test suite
bash tools/scripts/run_specific_test.sh <test_name>
```

## Maintenance

When adding new tools:
1. Place in appropriate subdirectory
2. Add description to this README
3. Include usage examples
4. Document any dependencies

---

*Last Updated: November 2024 during root directory cleanup*
