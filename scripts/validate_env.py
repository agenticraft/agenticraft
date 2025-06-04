#!/usr/bin/env python3
"""Validate AgentiCraft development environment."""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version is 3.10+."""
    print("Checking Python version... ", end="")
    if sys.version_info < (3, 10):
        print(f"❌ Python 3.10+ required, found {sys.version}")
        return False
    print(f"✅ {sys.version.split()[0]}")
    return True


def check_package_installed(package):
    """Check if a package is installed."""
    try:
        __import__(package)
        return True
    except ImportError:
        return False


def check_dependencies():
    """Check required dependencies are installed."""
    print("\nChecking dependencies:")
    
    required = [
        ("agenticraft", "AgentiCraft"),
        ("pydantic", "Pydantic"),
        ("httpx", "HTTPX"),
        ("pytest", "Pytest"),
        ("black", "Black"),
        ("ruff", "Ruff"),
        ("mypy", "MyPy"),
    ]
    
    all_good = True
    for package, name in required:
        print(f"  {name}... ", end="")
        if check_package_installed(package):
            print("✅")
        else:
            print("❌")
            all_good = False
    
    return all_good


def check_environment_files():
    """Check required files and directories exist."""
    print("\nChecking environment files:")
    
    required_files = [
        (".env", "Environment configuration"),
        ("pyproject.toml", "Project configuration"),
        ("setup.py", "Setup script"),
    ]
    
    required_dirs = [
        ("agenticraft", "Source directory"),
        ("tests", "Test directory"),
        ("docs", "Documentation directory"),
    ]
    
    all_good = True
    
    for file, desc in required_files:
        print(f"  {desc}... ", end="")
        if Path(file).exists():
            print("✅")
        else:
            print("❌")
            all_good = False
    
    for dir, desc in required_dirs:
        print(f"  {desc}... ", end="")
        if Path(dir).is_dir():
            print("✅")
        else:
            print("❌")
            all_good = False
    
    return all_good


def check_git_hooks():
    """Check if pre-commit hooks are installed."""
    print("\nChecking Git hooks... ", end="")
    if Path(".git/hooks/pre-commit").exists():
        print("✅")
        return True
    else:
        print("❌ Run 'pre-commit install'")
        return False


def main():
    """Run all checks."""
    print("🔍 AgentiCraft Development Environment Validation\n")
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_environment_files(),
        check_git_hooks(),
    ]
    
    if all(checks):
        print("\n✅ All checks passed! Environment is ready.")
        print("\nNext steps:")
        print("  1. Run 'make test' to run tests")
        print("  2. Run 'make docs-serve' to view documentation")
        print("  3. Happy coding! 🎉")
        return 0
    else:
        print("\n❌ Some checks failed. Run 'make setup' to fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
