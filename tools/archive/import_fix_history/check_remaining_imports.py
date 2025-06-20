#!/usr/bin/env python3
"""
Quick check for remaining import issues after fixes.
"""

import subprocess
import re
from pathlib import Path

def run_pytest_collect():
    """Run pytest collection and capture import errors."""
    print("Running pytest collection to find import errors...")
    print("=" * 80)
    
    result = subprocess.run(
        ["python", "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd="/Users/zahere/Desktop/TLV/agenticraft"
    )
    
    # Parse output for import errors
    import_errors = []
    current_file = None
    
    for line in result.stderr.split('\n'):
        # Look for file paths
        if "ERROR collecting" in line:
            match = re.search(r'ERROR collecting (.+\.py)', line)
            if match:
                current_file = match.group(1)
        
        # Look for ImportError lines
        if "ImportError:" in line and current_file:
            import_errors.append({
                'file': current_file,
                'error': line.strip()
            })
    
    return import_errors

def main():
    errors = run_pytest_collect()
    
    if not errors:
        print("✅ No import errors found during test collection!")
        return
    
    print(f"❌ Found {len(errors)} import errors:\n")
    
    # Group by error message
    error_groups = {}
    for error in errors:
        msg = error['error']
        if msg not in error_groups:
            error_groups[msg] = []
        error_groups[msg].append(error['file'])
    
    # Display grouped errors
    for error_msg, files in error_groups.items():
        print(f"\n{error_msg}")
        print(f"Affects {len(files)} files:")
        for file in files[:5]:  # Show first 5
            print(f"  - {file}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"  Total unique import errors: {len(error_groups)}")
    print(f"  Total affected test files: {len(errors)}")

if __name__ == '__main__':
    main()
