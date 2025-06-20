#!/usr/bin/env python3
"""
Cleanup script for removing redundant files after refactoring.

This script safely removes files and directories that are redundant
after the protocol and fabric refactoring.

Usage:
    python cleanup_redundant.py [--dry-run] [--backup]
"""

import os
import shutil
import argparse
from datetime import datetime
from pathlib import Path


# Directories to delete entirely
DIRS_TO_DELETE = [
    "agenticraft/protocols/mcp/transport",
    "agenticraft/protocols/mcp/auth", 
    "agenticraft/protocols/a2a/centralized",
    "agenticraft/protocols/a2a/decentralized",
    "agenticraft/protocols/a2a/hybrid",
    # "agenticraft/security/authentication",
    # "agenticraft/security/authorization",
    # "agenticraft/fabric/adapters",
    "agenticraft/protocols/base_backup",
    "agenticraft/protocols/bridges",
    # "agenticraft/protocols/external",
    # "agenticraft/core/streaming",  # empty directory
]

# Individual files to delete
FILES_TO_DELETE = [
    # "agenticraft/protocols/mcp/decorators.py",
    # "agenticraft/security/auth.py",
    "agenticraft/fabric/unified.py",
    "agenticraft/fabric/unified_enhanced.py", 
    "agenticraft/fabric/sdk_fabric.py",
    "agenticraft/fabric/adapters_base.py",
    # "agenticraft/utils/config.py",
]

# Files to review (not automatically deleted)
FILES_TO_REVIEW = [
    "agenticraft/agents/patterns/",
    "agenticraft/security/middleware.py",
    "agenticraft/security/sandbox/",
    "agenticraft/security/audit/",
]


def create_backup(base_path: Path):
    """Create a backup of files before deletion."""
    backup_dir = base_path / f"backup_before_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(exist_ok=True)
    
    print(f"Creating backup in: {backup_dir}")
    
    # Backup directories
    for dir_path in DIRS_TO_DELETE:
        full_path = base_path / dir_path
        if full_path.exists():
            dest = backup_dir / dir_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(full_path, dest)
            print(f"  Backed up directory: {dir_path}")
    
    # Backup files
    for file_path in FILES_TO_DELETE:
        full_path = base_path / file_path
        if full_path.exists():
            dest = backup_dir / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full_path, dest)
            print(f"  Backed up file: {file_path}")
    
    return backup_dir


def delete_files(base_path: Path, dry_run: bool = False):
    """Delete redundant files and directories."""
    print("\nDeleting redundant files and directories...")
    
    # Delete directories
    for dir_path in DIRS_TO_DELETE:
        full_path = base_path / dir_path
        if full_path.exists():
            if dry_run:
                print(f"  Would delete directory: {dir_path}")
            else:
                shutil.rmtree(full_path)
                print(f"  Deleted directory: {dir_path}")
        else:
            print(f"  Directory not found: {dir_path}")
    
    # Delete files
    for file_path in FILES_TO_DELETE:
        full_path = base_path / file_path
        if full_path.exists():
            if dry_run:
                print(f"  Would delete file: {file_path}")
            else:
                full_path.unlink()
                print(f"  Deleted file: {file_path}")
        else:
            print(f"  File not found: {file_path}")
    
    # Remove empty __pycache__ directories
    if not dry_run:
        for pycache in base_path.rglob("__pycache__"):
            if not any(pycache.iterdir()):
                pycache.rmdir()
                print(f"  Removed empty directory: {pycache.relative_to(base_path)}")


def show_files_to_review(base_path: Path):
    """Show files that need manual review."""
    print("\nFiles/directories to manually review:")
    for path in FILES_TO_REVIEW:
        full_path = base_path / path
        if full_path.exists():
            print(f"  - {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up redundant files after refactoring"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--backup",
        action="store_true", 
        help="Create a backup before deleting files"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path of the AgentiCraft project (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Verify we're in the right directory
    if not (args.base_path / "agenticraft").exists():
        print("Error: 'agenticraft' directory not found in the base path.")
        print("Please run this script from the AgentiCraft project root.")
        return 1
    
    print(f"AgentiCraft Cleanup Tool")
    print(f"Base path: {args.base_path}")
    print(f"Dry run: {args.dry_run}")
    print(f"Create backup: {args.backup}")
    print()
    
    # Create backup if requested
    if args.backup and not args.dry_run:
        backup_dir = create_backup(args.base_path)
        print(f"\nBackup created at: {backup_dir}")
    
    # Delete files
    delete_files(args.base_path, args.dry_run)
    
    # Show files to review
    show_files_to_review(args.base_path)
    
    if args.dry_run:
        print("\nThis was a dry run. No files were actually deleted.")
        print("Run without --dry-run to perform the deletion.")
    else:
        print("\nCleanup complete!")
        print("Remember to:")
        print("  1. Run tests to ensure nothing is broken")
        print("  2. Update any remaining imports in tests/examples")
        print("  3. Review the files listed above for any unique functionality")
    
    return 0


if __name__ == "__main__":
    exit(main())
