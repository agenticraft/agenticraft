#!/usr/bin/env python3
"""Run tests for core modules with minimal output."""
import subprocess
import sys
import os

os.chdir('/Users/zahere/Desktop/TLV/agenticraft')

# Run core module tests only
test_files = [
    "tests/test_config.py",
    "tests/test_exceptions.py",
    "tests/test_plugin_comprehensive.py",
    "tests/test_types.py",
    "tests/test_provider_comprehensive.py",
    "tests/test_telemetry_comprehensive.py"
]

cmd = [
    sys.executable, "-m", "pytest"
] + test_files + [
    "-v", "--tb=short", 
    "--disable-warnings",  # Disable warnings for now
    "-x"  # Stop on first failure
]

print("🧪 Running Core Module Tests")
print("=" * 60)

result = subprocess.run(cmd)
sys.exit(result.returncode)
