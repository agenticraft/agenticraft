#!/usr/bin/env python3
"""
Test runner to verify import fixes.
"""

import subprocess
import sys
import os

def run_tests():
    """Run tests on files that had import errors."""
    
    # Change to project directory
    os.chdir("/Users/zahere/Desktop/TLV/agenticraft")
    
    # Test files that were having import issues
    test_groups = {
        "Workflow Tests": [
            "tests/workflows/test_templates.py",
            "tests/workflows/test_visualizer.py",
            "tests/workflows/test_patterns.py",
        ],
        "Fabric Tests": [
            "tests/fabric/test_unified.py",
            "tests/fabric/test_sdk_integration.py",
            "tests/fabric/test_decorators.py",
            "tests/fabric/test_enhanced_fabric.py",
        ],
        "CLI Tests": [
            "tests/unit/cli/test_main.py",
        ]
    }
    
    print("AgentiCraft Import Fix Test Runner")
    print("=" * 60)
    
    overall_passed = True
    
    for group_name, test_files in test_groups.items():
        print(f"\n{group_name}:")
        print("-" * 40)
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                print(f"  ❌ {test_file} - NOT FOUND")
                continue
            
            # Run pytest on the file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-x", test_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Count passed tests
                output = result.stdout
                passed = output.count(" PASSED")
                print(f"  ✅ {test_file} - {passed} tests passed")
            else:
                overall_passed = False
                # Check if it's an import error
                if "ImportError" in result.stderr:
                    for line in result.stderr.split('\n'):
                        if "ImportError:" in line:
                            print(f"  ❌ {test_file} - IMPORT ERROR")
                            print(f"     {line.strip()}")
                            break
                else:
                    # Other error
                    print(f"  ❌ {test_file} - FAILED")
                    # Try to extract the failure reason
                    if "FAILED" in result.stdout:
                        for line in result.stdout.split('\n'):
                            if "FAILED" in line or "ERROR" in line:
                                print(f"     {line.strip()}")
                                break
    
    print("\n" + "=" * 60)
    if overall_passed:
        print("✅ All import issues appear to be fixed!")
    else:
        print("❌ Some issues remain - check the errors above")
    
    print("\nTo run all tests with verbose output:")
    print("  pytest -xvs")
    
    print("\nTo run a specific failing test:")
    print("  pytest -xvs path/to/test_file.py::test_name")

if __name__ == '__main__':
    run_tests()
