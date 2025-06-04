#!/usr/bin/env python3
"""Run core module tests only."""
import subprocess
import sys
import os

os.chdir('/Users/zahere/Desktop/TLV/agenticraft')

# Run only core module tests
cmd = [
    sys.executable, "-m", "pytest", 
    "tests/test_config.py",
    "tests/test_exceptions.py", 
    "tests/test_plugin_comprehensive.py",
    "tests/test_types.py",
    "-v", "--tb=short"
]

print("🧪 Running Core Module Tests")
print("=" * 60)
print(f"Command: {' '.join(cmd)}")
print("=" * 60)

result = subprocess.run(cmd)
sys.exit(result.returncode)
