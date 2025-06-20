#!/usr/bin/env python3
"""Final verification of security module fixes."""

import subprocess
import sys
import os

print("=" * 70)
print("SECURITY MODULE VERIFICATION")
print("=" * 70)

# Change to project directory
os.chdir("/Users/zahere/Desktop/TLV/agenticraft")

# Test 1: Import test
print("\n1. Testing imports...")
import_test = """
from agenticraft.security import (
    SandboxManager, SecurityContext, SandboxType,
    AuthenticationError, AuthorizationError
)
from agenticraft.core.auth import AuthConfig, AuthProvider
print("✅ All imports successful")
"""

result = subprocess.run([sys.executable, "-c", import_test], capture_output=True, text=True)
print(result.stdout if result.returncode == 0 else f"❌ Import failed: {result.stderr}")

# Test 2: Run security tests
print("\n2. Running security tests...")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-xvs", "tests/security/test_sandbox.py", "-k", "not agent"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ All sandbox tests passed!")
else:
    print("❌ Some tests failed:")
    # Extract just the test results
    for line in result.stdout.split('\n'):
        if '::' in line or 'PASSED' in line or 'FAILED' in line or 'SKIPPED' in line:
            print(f"   {line}")

# Test 3: Check for remaining issues
print("\n3. Checking for remaining import errors...")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "tests/security/"],
    capture_output=True,
    text=True
)

if "ModuleNotFoundError" in result.stderr or "ImportError" in result.stderr:
    print("❌ Import errors still exist:")
    print(result.stderr)
else:
    print("✅ No import errors detected")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
