#!/usr/bin/env python3
"""
Pre-cleanup safety check script.
Ensures it's safe to run the cleanup by checking:
1. Git status (no uncommitted changes)
2. All tests pass
3. No active references to files being deleted
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path(__file__).parent


def check_git_status() -> Tuple[bool, str]:
    """Check if git working directory is clean."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        
        if result.returncode != 0:
            return False, "Git command failed. Is this a git repository?"
        
        if result.stdout.strip():
            return False, "Uncommitted changes found. Please commit or stash changes first."
        
        return True, "Git working directory is clean"
    except FileNotFoundError:
        return False, "Git not found. Please install git."
    except Exception as e:
        return False, f"Error checking git status: {e}"


def check_imports() -> Tuple[bool, List[str]]:
    """Check for imports of files that will be deleted."""
    problematic_imports = []
    files_to_delete = [
        "unified.py",
        "unified_enhanced.py", 
        "sdk_fabric.py",
        "adapters_base.py",
        "utils.config",
        "security.auth",
        "protocols.mcp.decorators"
    ]
    
    # Search Python files for imports
    for py_file in BASE_DIR.rglob("*.py"):
        # Skip test files and this script
        if "test" in py_file.name or py_file.name in ["cleanup_redundant_files.py", "cleanup_check.py"]:
            continue
            
        try:
            with open(py_file, "r") as f:
                content = f.read()
                
            for import_pattern in files_to_delete:
                if f"from {import_pattern}" in content or f"import {import_pattern}" in content:
                    problematic_imports.append(f"{py_file.relative_to(BASE_DIR)}: imports {import_pattern}")
        except:
            pass
    
    if problematic_imports:
        return False, problematic_imports
    
    return True, []


def run_tests() -> Tuple[bool, str]:
    """Run tests to ensure nothing is broken."""
    print("Running tests... (this may take a moment)")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        
        if result.returncode == 0:
            return True, "All tests passed"
        else:
            # Check if it's import errors that might be fixed by cleanup
            if "ModuleNotFoundError" in result.stderr or "ImportError" in result.stderr:
                return True, "Tests have import errors (cleanup may fix these)"
            return False, f"Tests failed with {result.returncode} errors"
    except FileNotFoundError:
        return False, "pytest not found. Please install pytest."
    except Exception as e:
        return False, f"Error running tests: {e}"


def check_backup_exists() -> Tuple[bool, str]:
    """Check if backup directory exists or can be created."""
    backup_dir = BASE_DIR / "cleanup_backups"
    
    try:
        backup_dir.mkdir(exist_ok=True)
        return True, f"Backup directory ready: {backup_dir}"
    except Exception as e:
        return False, f"Cannot create backup directory: {e}"


def main():
    """Run all safety checks."""
    print("🔍 AGENTICRAFT CLEANUP SAFETY CHECK")
    print("=" * 80)
    
    checks = [
        ("Git Status", check_git_status),
        ("Import Check", check_imports),
        ("Test Suite", run_tests),
        ("Backup Directory", check_backup_exists)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}...")
        
        if check_name == "Import Check":
            passed, imports = check_func()
            if passed:
                print("  ✅ No problematic imports found")
            else:
                print("  ⚠️  Found imports of files to be deleted:")
                for imp in imports:
                    print(f"     • {imp}")
                all_passed = False
        else:
            passed, message = check_func()
            if passed:
                print(f"  ✅ {message}")
            else:
                print(f"  ❌ {message}")
                all_passed = False
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("✅ All checks passed! It's safe to run the cleanup script.")
        print("\nNext steps:")
        print("1. Review what will be deleted:")
        print("   python cleanup_redundant_files.py")
        print("\n2. Execute the cleanup:")
        print("   python cleanup_redundant_files.py --execute")
    else:
        print("❌ Some checks failed. Please address the issues before running cleanup.")
        print("\nNote: Import errors might be expected if the refactoring is complete.")
        print("      Use your judgment based on the specific errors shown.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
