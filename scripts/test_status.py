#!/usr/bin/env python3
"""Quick test status check."""
import subprocess
import sys
import os

os.chdir('/Users/zahere/Desktop/TLV/agenticraft')

# Run pytest with collection summary
cmd = [
    sys.executable, "-m", "pytest",
    "--collect-only", "-q"
]

print("🧪 Test Collection Summary")
print("=" * 60)

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Now run core tests
print("\n" + "=" * 60)
print("🧪 Running Core Module Tests")
print("=" * 60)

core_tests = [
    "tests/test_config.py",
    "tests/test_exceptions_comprehensive.py", 
    "tests/test_plugin_comprehensive.py",
    "tests/test_types_comprehensive.py",
    "tests/test_provider_comprehensive.py",
    "tests/test_telemetry_comprehensive.py",
    "tests/test_tool_comprehensive.py",
    "tests/test_workflow.py"  # Added workflow tests
]

cmd = [sys.executable, "-m", "pytest"] + core_tests + ["-v", "--tb=short", "-x"]
result = subprocess.run(cmd)
sys.exit(result.returncode)
