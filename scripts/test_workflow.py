#!/usr/bin/env python3
"""Quick workflow test check."""
import subprocess
import sys
import os

# Change to project directory
os.chdir('/Users/zahere/Desktop/TLV/agenticraft')

print("🧪 Testing Workflow Import and Tests")
print("=" * 60)

# First test if we can import Workflow
print("\n1. Testing import...")
try:
    from agenticraft import Workflow, Step
    print("✅ Import successful: Workflow and Step imported correctly")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Now run the workflow tests
print("\n2. Running workflow tests...")
print("=" * 60)

cmd = [sys.executable, "-m", "pytest", "tests/test_workflow.py", "-v", "--tb=short"]
result = subprocess.run(cmd)

print("\n" + "=" * 60)
if result.returncode == 0:
    print("✅ All workflow tests passed!")
else:
    print("❌ Some workflow tests failed")
    
sys.exit(result.returncode)
