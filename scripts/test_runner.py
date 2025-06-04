#!/usr/bin/env python3
"""
AgentiCraft Test Runner

Run tests for specific modules or all tests with coverage reporting.
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)


def run_tests(test_target, coverage=True, verbose=True):
    """Run pytest with specified options."""
    cmd = [sys.executable, "-m", "pytest"]
    
    if test_target:
        cmd.append(test_target)
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=agenticraft", "--cov-report=term-missing"])
    
    cmd.append("--tb=short")
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run AgentiCraft tests")
    parser.add_argument(
        "target",
        nargs="?",
        help="Test file or directory to run (default: all tests)"
    )
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Run without coverage reporting"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Run in quiet mode"
    )
    
    args = parser.parse_args()
    
    success = run_tests(
        test_target=args.target,
        coverage=not args.no_cov,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
