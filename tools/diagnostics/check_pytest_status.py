#!/usr/bin/env python3
"""Run pytest with brief output to check current status."""

import subprocess
import sys

print("Running pytest to check current status...")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "-xvs", "--tb=short", "--maxfail=3"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Check for specific import errors
if "ImportError" in result.stdout or "ModuleNotFoundError" in result.stdout:
    print("\n❌ Import errors still present")
else:
    print("\n✅ No import errors detected")

sys.exit(result.returncode)
