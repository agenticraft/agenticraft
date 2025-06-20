#!/usr/bin/env python3
"""Run just the agent security tests."""

import subprocess
import sys
import os

os.chdir("/Users/zahere/Desktop/TLV/agenticraft")

print("Running agent security tests...")
print("=" * 70)

# Run just the agent tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-xvs", 
     "tests/security/test_sandbox.py::TestSandboxSecurity::test_agent_secure_execution",
     "tests/security/test_sandbox.py::TestSandboxSecurity::test_agent_secure_tool_execution"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

print("\n" + "=" * 70)

if result.returncode == 0:
    print("✅ Agent security tests passed!")
else:
    print("❌ Agent security tests failed")
    # Extract the failure reason
    for line in result.stdout.split('\n'):
        if 'FAILED' in line or 'ERROR' in line or 'assert' in line:
            print(f"   {line.strip()}")
