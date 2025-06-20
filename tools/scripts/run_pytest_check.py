#!/usr/bin/env python3
"""Quick test to verify the import fix worked."""

print("Running pytest to check if import error is fixed...")
import subprocess
import sys

result = subprocess.run([sys.executable, "-m", "pytest", "-xvs", "--tb=short"], 
                       capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print(result.stderr)

if "ModuleNotFoundError: No module named 'agenticraft.fabric.agent_enhanced'" not in result.stdout:
    print("\n✅ Import error appears to be fixed!")
else:
    print("\n❌ Import error still present")

sys.exit(result.returncode)
