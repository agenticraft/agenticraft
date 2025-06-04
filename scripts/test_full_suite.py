#!/usr/bin/env python3
"""Run tests without stopping on errors to see all issues."""
import subprocess
import sys
import os

os.chdir('/Users/zahere/Desktop/TLV/agenticraft')

# Run tests with continue-on-error to see all issues
cmd = [
    sys.executable, "-m", "pytest", 
    "-v", "--tb=short", "--continue-on-collection-errors",
    "--cov=agenticraft", "--cov-report=term-missing:skip-covered"
]

print("🧪 Running Full Test Suite")
print("=" * 60)
print(f"Command: {' '.join(cmd)}")
print("=" * 60)

result = subprocess.run(cmd)
sys.exit(result.returncode)
