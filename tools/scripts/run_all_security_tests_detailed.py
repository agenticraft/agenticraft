#!/usr/bin/env python3
"""Run all security tests with detailed output."""

import subprocess
import sys
import os

os.chdir("/Users/zahere/Desktop/TLV/agenticraft")

print("Running ALL security sandbox tests...")
print("=" * 70)

# Run all tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-xvs", "tests/security/test_sandbox.py"],
    capture_output=True,
    text=True
)

# Print full output
print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

print("\n" + "=" * 70)

# Parse results
lines = result.stdout.split('\n')
test_results = []

for line in lines:
    if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
        test_name = line.split('::')[-1].split()[0]
        status = 'PASSED' if 'PASSED' in line else ('FAILED' if 'FAILED' in line else 'SKIPPED')
        test_results.append((test_name, status))

print("\nTEST SUMMARY:")
print("-" * 40)
for test_name, status in test_results:
    emoji = "✅" if status == "PASSED" else ("❌" if status == "FAILED" else "⚠️")
    print(f"{emoji} {test_name}: {status}")

print("-" * 40)
if result.returncode == 0:
    print("🎉 All tests passed!")
else:
    print(f"💔 {sum(1 for _, s in test_results if s == 'FAILED')} test(s) failed")
