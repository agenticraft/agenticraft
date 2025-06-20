#!/usr/bin/env python3
"""
Final verification of import fixes.
"""

import subprocess
import sys
import os

def check_imports():
    """Check if all import issues are resolved."""
    
    os.chdir("/Users/zahere/Desktop/TLV/agenticraft")
    
    print("AgentiCraft Import Fix Verification")
    print("=" * 60)
    
    # First, try importing the problematic modules directly
    print("\n1. Testing direct imports:")
    print("-" * 40)
    
    test_imports = [
        ("Core BaseTool", "from agenticraft.core import BaseTool"),
        ("Core WorkflowConfig", "from agenticraft.core import WorkflowConfig"),
        ("Auth JWTAuth", "from agenticraft.core.auth import JWTAuth"),
        ("Auth APIKeyAuth", "from agenticraft.core.auth import APIKeyAuth"),
        ("Fabric Unified", "from agenticraft.fabric.agent import UnifiedProtocolFabric"),
    ]
    
    for name, import_stmt in test_imports:
        try:
            exec(import_stmt)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
    
    # Run pytest collection to check for import errors
    print("\n\n2. Running pytest collection:")
    print("-" * 40)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--tb=no"],
        capture_output=True,
        text=True
    )
    
    # Count collected tests
    stdout_lines = result.stdout.strip().split('\n')
    test_count = 0
    for line in stdout_lines:
        if " passed" in line or " deselected" in line:
            continue
        if "::" in line:
            test_count += 1
    
    print(f"  ✅ Collected {test_count} tests")
    
    # Check for import errors in stderr
    if "ImportError" in result.stderr:
        print("\n  ❌ Import errors found:")
        for line in result.stderr.split('\n'):
            if "ImportError:" in line:
                print(f"     {line.strip()}")
    else:
        print("  ✅ No import errors during collection")
    
    # Check specific test files
    print("\n\n3. Checking key test files:")
    print("-" * 40)
    
    key_tests = [
        "tests/fabric/test_unified.py",
        "tests/workflows/test_templates.py",
        "tests/unit/cli/test_main.py"
    ]
    
    for test_file in key_tests:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", test_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Count tests in file
            test_count = result.stdout.count("::")
            print(f"  ✅ {test_file} - {test_count} tests collected")
        else:
            if "ImportError" in result.stderr:
                print(f"  ❌ {test_file} - Import error")
            else:
                print(f"  ❌ {test_file} - Collection failed")
    
    print("\n" + "=" * 60)
    print("Import fix verification complete!")
    print("\nNext step: Run actual tests with:")
    print("  pytest -xvs")

if __name__ == '__main__':
    check_imports()
