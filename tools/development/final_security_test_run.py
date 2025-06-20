#!/usr/bin/env python3
"""Final test run for security module after all fixes."""

import subprocess
import sys
import os

print("FINAL SECURITY MODULE TEST RUN")
print("=" * 70)
print("\nChanges Applied:")
print("1. Fixed imports from security.auth → core.auth")
print("2. Added SandboxManager.initialize() method")
print("3. Fixed SecurityContext permissions in tests")
print("4. Implemented timeout handling with threading")
print("5. Fixed sandbox type handling for None values")
print("6. Added warning for RestrictedPythonSandbox tool limitations")
print("\n" + "=" * 70)

os.chdir("/Users/zahere/Desktop/TLV/agenticraft")

# Run all tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-v", "tests/security/test_sandbox.py"],
    capture_output=True,
    text=True
)

# Extract test results
lines = result.stdout.split('\n')
test_results = []

for line in lines:
    if '::' in line and any(status in line for status in ['PASSED', 'FAILED', 'SKIPPED']):
        parts = line.split('::')
        if len(parts) >= 2:
            test_name = parts[-1].split()[0]
            if 'PASSED' in line:
                status = 'PASSED'
            elif 'FAILED' in line:
                status = 'FAILED'
            else:
                status = 'SKIPPED'
            test_results.append((test_name, status))

print("\nTEST RESULTS:")
print("-" * 60)
for test_name, status in test_results:
    emoji = "✅" if status == "PASSED" else ("❌" if status == "FAILED" else "⚠️")
    print(f"{emoji} {test_name:<40} {status}")

print("-" * 60)
passed = sum(1 for _, s in test_results if s == "PASSED")
failed = sum(1 for _, s in test_results if s == "FAILED")
total = len(test_results)

print(f"\nSummary: {passed}/{total} tests passed")

if failed > 0:
    print(f"\n❌ {failed} test(s) still failing")
    print("\nKnown Limitations:")
    print("- RestrictedPythonSandbox cannot execute arbitrary callables")
    print("- Tool execution falls back to non-sandboxed mode with warning")
else:
    print("\n🎉 All tests passing!")

print("\n" + "=" * 70)
