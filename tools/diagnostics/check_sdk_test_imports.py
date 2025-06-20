#!/usr/bin/env python3
"""Test if the SDK integration test imports work."""

import sys
import subprocess

print("Checking SDK integration test imports...")
print("=" * 60)

# Run pytest with collect-only to check imports
result = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "tests/test_sdk_integration.py"],
    cwd="/Users/zahere/Desktop/TLV/agenticraft",
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ SDK integration test imports successfully!")
    print("\nTests collected:")
    for line in result.stdout.split('\n'):
        if '<Function' in line or '<Class' in line:
            print(f"  {line.strip()}")
else:
    print("❌ Import error detected:")
    print(result.stderr)
    if "ImportError" in result.stderr:
        for line in result.stderr.split('\n'):
            if 'ImportError' in line or 'cannot import' in line:
                print(f"  → {line.strip()}")
