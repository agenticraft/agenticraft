#!/usr/bin/env python3
"""Run all core module tests."""
import subprocess
import sys
import os

os.chdir('/Users/zahere/Desktop/TLV/agenticraft')

test_files = [
    "tests/test_exceptions.py",
    "tests/test_plugin_comprehensive.py", 
    "tests/test_types.py",
    "tests/test_config.py"
]

print("🧪 Running all core module tests")
print("=" * 60)

all_passed = True
results = {}

for test_file in test_files:
    print(f"\n📁 Running {test_file}...")
    print("-" * 40)
    
    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Count passed tests
        import re
        matches = re.findall(r'(\d+) passed', result.stdout)
        if matches:
            count = matches[-1]
            results[test_file] = f"✅ {count} tests passed"
            print(f"✅ All tests passed!")
        else:
            results[test_file] = "✅ Tests passed"
    else:
        results[test_file] = "❌ Some tests failed"
        all_passed = False
        print(f"❌ Tests failed!")
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

print("\n" + "=" * 60)
print("📊 Summary")
print("=" * 60)

for test_file, status in results.items():
    print(f"{test_file:<40} {status}")

print("\n" + "=" * 60)
if all_passed:
    print("✅ All tests passed!")
else:
    print("❌ Some tests need attention")
