#!/usr/bin/env python3
"""
Generate test report for all core modules.
"""
import subprocess
import sys
import os
from pathlib import Path
import re

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Core module test files
CORE_TESTS = [
    ("Config", "tests/test_config.py"),
    ("Exceptions", "tests/test_exceptions.py"),
    ("Plugin", "tests/test_plugin_comprehensive.py"),
    ("Types", "tests/test_types.py"),
]


def run_test_file(test_file):
    """Run a single test file and return results."""
    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse results
    passed = 0
    failed = 0
    errors = 0
    
    # Look for test results in output
    if "passed" in result.stdout:
        match = re.search(r'(\d+) passed', result.stdout)
        if match:
            passed = int(match.group(1))
    
    if "failed" in result.stdout:
        match = re.search(r'(\d+) failed', result.stdout)
        if match:
            failed = int(match.group(1))
    
    if "error" in result.stdout:
        match = re.search(r'(\d+) error', result.stdout)
        if match:
            errors = int(match.group(1))
    
    return {
        'passed': passed,
        'failed': failed,
        'errors': errors,
        'success': result.returncode == 0
    }


def main():
    print("🧪 AgentiCraft Core Module Test Report")
    print("=" * 60)
    print()
    
    results = []
    total_passed = 0
    total_failed = 0
    total_errors = 0
    all_success = True
    
    for module_name, test_file in CORE_TESTS:
        print(f"Testing {module_name}...", end=" ", flush=True)
        
        result = run_test_file(test_file)
        results.append((module_name, result))
        
        total_passed += result['passed']
        total_failed += result['failed']
        total_errors += result['errors']
        
        if result['success']:
            print(f"✅ {result['passed']} passed")
        else:
            print(f"❌ {result['passed']} passed, {result['failed']} failed, {result['errors']} errors")
            all_success = False
    
    print()
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print()
    
    # Detailed results table
    print(f"{'Module':<15} {'Passed':<10} {'Failed':<10} {'Errors':<10} {'Status':<10}")
    print("-" * 55)
    
    for module_name, result in results:
        status = "✅ OK" if result['success'] else "❌ FAIL"
        print(f"{module_name:<15} {result['passed']:<10} {result['failed']:<10} {result['errors']:<10} {status:<10}")
    
    print("-" * 55)
    print(f"{'TOTAL':<15} {total_passed:<10} {total_failed:<10} {total_errors:<10}")
    
    print()
    print("=" * 60)
    
    if all_success:
        print("✅ All core module tests passing!")
        print(f"🎉 Total: {total_passed} tests passed")
    else:
        print("❌ Some tests need attention")
        print(f"📊 {total_passed} passed, {total_failed} failed, {total_errors} errors")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
