#!/usr/bin/env python3
"""Run security tests and show results."""

import subprocess
import sys
import os

os.chdir("/Users/zahere/Desktop/TLV/agenticraft")

print("Running security sandbox tests...")
print("=" * 70)

# Run all tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-xvs", "tests/security/test_sandbox.py"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

print("\n" + "=" * 70)

# Summary
if result.returncode == 0:
    print("✅ All security tests passed!")
else:
    print("❌ Some tests failed")
    # Count passed/failed
    passed = result.stdout.count("PASSED")
    failed = result.stdout.count("FAILED")
    print(f"Passed: {passed}, Failed: {failed}")
