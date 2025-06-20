#!/usr/bin/env python3
"""Run all security sandbox tests and show results."""

import subprocess
import sys

print("Running all security sandbox tests...")
print("=" * 70)

# Run pytest with verbose output
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-xvs", "tests/security/test_sandbox.py"],
    cwd="/Users/zahere/Desktop/TLV/agenticraft",
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

print("\n" + "=" * 70)
if result.returncode == 0:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed")
    print(f"Return code: {result.returncode}")
