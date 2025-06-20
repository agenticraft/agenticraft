#!/usr/bin/env python3
"""
Quick check for remaining import issues after fixes.
"""

import subprocess
import sys
import os

def check_imports():
    """Run a quick import check on key test files."""
    test_files = [
        "tests/workflows/test_templates.py",
        "tests/workflows/test_visualizer.py", 
        "tests/workflows/test_patterns.py",
        "tests/unit/cli/test_main.py",
        "tests/fabric/test_unified.py"
    ]
    
    os.chdir("/Users/zahere/Desktop/TLV/agenticraft")
    
    print("Checking imports in key test files...")
    print("=" * 60)
    
    errors = []
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"❌ {test_file} - FILE NOT FOUND")
            continue
            
        # Try to run pytest collection on the file
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", test_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Extract import error if present
            stderr = result.stderr
            if "ImportError" in stderr:
                # Find the actual import error line
                for line in stderr.split('\n'):
                    if "ImportError:" in line:
                        errors.append((test_file, line.strip()))
                        print(f"❌ {test_file}")
                        print(f"   {line.strip()}")
                        break
            else:
                print(f"❌ {test_file} - OTHER ERROR")
        else:
            print(f"✅ {test_file} - OK")
    
    print("\n" + "=" * 60)
    if errors:
        print(f"Found {len(errors)} files with import errors")
    else:
        print("All checked files have working imports!")

if __name__ == '__main__':
    check_imports()
