#!/usr/bin/env python3
"""Check if pytest can import the security test module."""

import subprocess
import sys

print("Checking if pytest can import security test module...")
print("-" * 60)

# Run pytest with dry-run to just collect tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "tests/security/test_sandbox.py"],
    cwd="/Users/zahere/Desktop/TLV/agenticraft",
    capture_output=True,
    text=True
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)

if result.returncode == 0:
    print("\n✅ Security test module can be imported successfully!")
else:
    print("\n❌ Import still failing")
