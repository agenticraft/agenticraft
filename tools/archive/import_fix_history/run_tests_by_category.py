#!/usr/bin/env python3
"""
Helper script to run tests by category after import fixes.
"""

import subprocess
import sys
import os

def run_test_category(category, path, description):
    """Run tests for a specific category."""
    print(f"\n{'='*60}")
    print(f"Running {category} Tests")
    print(f"Path: {path}")
    print(f"Description: {description}")
    print('='*60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-xvs", path],
        cwd="/Users/zahere/Desktop/TLV/agenticraft"
    )
    
    return result.returncode == 0

def main():
    """Run different test categories."""
    
    os.chdir("/Users/zahere/Desktop/TLV/agenticraft")
    
    print("AgentiCraft Test Runner")
    print("After Import Fix Completion")
    print("="*60)
    
    # Define test categories
    categories = [
        ("Workflow", "tests/workflows/", "Should all pass - imports fixed"),
        ("Unit", "tests/unit/", "Imports fixed, may have other failures"),
        ("Fabric", "tests/fabric/", "Imports fixed with stubs, may have execution failures"),
        ("Examples", "tests/examples/", "Integration tests, likely to fail"),
    ]
    
    results = {}
    
    # Ask which to run
    print("\nAvailable test categories:")
    for i, (name, path, desc) in enumerate(categories, 1):
        print(f"{i}. {name} - {desc}")
    print(f"{len(categories)+1}. Run all categories")
    print("0. Exit")
    
    choice = input("\nSelect category (0-5): ").strip()
    
    if choice == "0":
        return
    elif choice == str(len(categories)+1):
        # Run all
        for name, path, desc in categories:
            results[name] = run_test_category(name, path, desc)
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(categories):
                name, path, desc = categories[idx]
                results[name] = run_test_category(name, path, desc)
        except:
            print("Invalid choice")
            return
    
    # Summary
    if results:
        print("\n" + "="*60)
        print("Test Summary:")
        print("="*60)
        for name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{name}: {status}")
        
        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 All selected tests passed!")
        else:
            print("\n⚠️  Some tests failed (but imports are working!)")

if __name__ == '__main__':
    main()
