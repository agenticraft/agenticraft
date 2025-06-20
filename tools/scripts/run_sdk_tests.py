#!/usr/bin/env python3
"""Run SDK integration tests to verify all are passing."""

import subprocess
import sys
import os

os.chdir("/Users/zahere/Desktop/TLV/agenticraft")

print("Running SDK Integration Tests")
print("=" * 60)

# Run all SDK integration tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-v", "tests/test_sdk_integration.py"],
    capture_output=True,
    text=True
)

# Print output
print(result.stdout)

# Extract summary
if result.returncode == 0:
    print("\n✅ All SDK integration tests passed!")
else:
    print("\n❌ Some tests failed")
    
# Count results
lines = result.stdout.split('\n')
for line in lines:
    if " passed" in line and " failed" in line:
        print(f"\nTest Summary: {line.strip()}")
        break
