#!/usr/bin/env python3
"""
Cleanup script to remove redundant files after AgentiCraft refactoring.
This script is based on REDUNDANT_FILES.md and will:
1. Create a backup list of files to be deleted
2. Show what will be deleted and ask for confirmation
3. Delete files and directories
4. Create a rollback script
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# Base directory
BASE_DIR = Path(__file__).parent

# Directories to delete (from REDUNDANT_FILES.md)
DIRECTORIES_TO_DELETE = [
    "protocols/mcp/transport",
    "protocols/mcp/auth", 
    "protocols/a2a/centralized",
    "protocols/a2a/decentralized",
    "protocols/a2a/hybrid",
    "security/authentication",
    "security/authorization",
    "fabric/adapters",  # Check if this still has needed files
    "protocols/base_backup",
    "protocols/bridges",
    "protocols/external",
    "core/streaming",  # Empty directory
]

# Individual files to delete
FILES_TO_DELETE = [
    "protocols/mcp/decorators.py",
    "security/auth.py",
    "fabric/unified.py",  # May already be deleted
    "fabric/unified_enhanced.py",  # May already be deleted
    "fabric/sdk_fabric.py",
    "fabric/adapters_base.py",
    "utils/config.py",
]

# Files/directories to review before deletion
FILES_TO_REVIEW = [
    ("agents/patterns", "Check if any patterns are unique vs /core/patterns/"),
    ("security/middleware.py", "Might have useful middleware to move to core"),
    ("security/sandbox", "Sandboxing functionality might be useful to keep"),
    ("security/audit", "Audit logging might be useful to move to core"),
]


class CleanupManager:
    def __init__(self, base_dir: Path, dry_run: bool = True):
        self.base_dir = base_dir
        self.dry_run = dry_run
        self.deleted_items = []
        self.skipped_items = []
        self.errors = []
        
    def check_exists(self, path: str) -> Tuple[bool, Path]:
        """Check if a path exists and return full path."""
        full_path = self.base_dir / path
        return full_path.exists(), full_path
    
    def scan_redundant_files(self) -> Dict[str, List[Tuple[str, Path]]]:
        """Scan for all redundant files and categorize them."""
        results = {
            "directories": [],
            "files": [],
            "missing": [],
            "review": []
        }
        
        # Check directories
        for dir_path in DIRECTORIES_TO_DELETE:
            exists, full_path = self.check_exists(dir_path)
            if exists:
                results["directories"].append((dir_path, full_path))
            else:
                results["missing"].append((dir_path, full_path))
        
        # Check individual files
        for file_path in FILES_TO_DELETE:
            exists, full_path = self.check_exists(file_path)
            if exists:
                results["files"].append((file_path, full_path))
            else:
                results["missing"].append((file_path, full_path))
        
        # Check files that need review
        for review_path, reason in FILES_TO_REVIEW:
            exists, full_path = self.check_exists(review_path)
            if exists:
                results["review"].append((review_path, full_path, reason))
        
        return results
    
    def show_summary(self, results: Dict[str, List]) -> None:
        """Display summary of what will be deleted."""
        print("=" * 80)
        print("REDUNDANT FILES CLEANUP SUMMARY")
        print("=" * 80)
        
        if results["directories"]:
            print(f"\n📁 DIRECTORIES TO DELETE ({len(results['directories'])})")
            print("-" * 40)
            for path, full_path in results["directories"]:
                size = self.get_dir_size(full_path)
                print(f"  • {path} ({self.format_size(size)})")
        
        if results["files"]:
            print(f"\n📄 FILES TO DELETE ({len(results['files'])})")
            print("-" * 40)
            for path, full_path in results["files"]:
                size = full_path.stat().st_size if full_path.exists() else 0
                print(f"  • {path} ({self.format_size(size)})")
        
        if results["missing"]:
            print(f"\n❌ ALREADY DELETED/MISSING ({len(results['missing'])})")
            print("-" * 40)
            for path, _ in results["missing"]:
                print(f"  • {path}")
        
        if results["review"]:
            print(f"\n⚠️  FILES TO REVIEW ({len(results['review'])})")
            print("-" * 40)
            for path, _, reason in results["review"]:
                print(f"  • {path}")
                print(f"    → {reason}")
        
        # Calculate total size
        total_size = 0
        for _, full_path in results["directories"]:
            total_size += self.get_dir_size(full_path)
        for _, full_path in results["files"]:
            if full_path.exists():
                total_size += full_path.stat().st_size
        
        print(f"\n📊 TOTAL SIZE TO BE FREED: {self.format_size(total_size)}")
        print("=" * 80)
    
    def get_dir_size(self, path: Path) -> int:
        """Calculate total size of a directory."""
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        except:
            pass
        return total
    
    def format_size(self, size: int) -> str:
        """Format size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def create_backup_manifest(self, results: Dict[str, List]) -> Path:
        """Create a manifest of files to be deleted."""
        manifest_dir = self.base_dir / "cleanup_backups"
        manifest_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_file = manifest_dir / f"cleanup_manifest_{timestamp}.json"
        
        manifest_data = {
            "timestamp": timestamp,
            "base_dir": str(self.base_dir),
            "directories": [str(p) for _, p in results["directories"]],
            "files": [str(p) for _, p in results["files"]],
            "review": [(str(p), reason) for _, p, reason in results["review"]]
        }
        
        with open(manifest_file, "w") as f:
            json.dump(manifest_data, f, indent=2)
        
        print(f"\n✅ Backup manifest created: {manifest_file}")
        return manifest_file
    
    def delete_items(self, results: Dict[str, List]) -> None:
        """Delete the redundant files and directories."""
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No files will be deleted")
            return
        
        print("\n🗑️  DELETING FILES...")
        
        # Delete individual files first
        for path, full_path in results["files"]:
            try:
                if full_path.exists():
                    full_path.unlink()
                    self.deleted_items.append(str(full_path))
                    print(f"  ✓ Deleted: {path}")
            except Exception as e:
                self.errors.append((path, str(e)))
                print(f"  ✗ Error deleting {path}: {e}")
        
        # Delete directories
        for path, full_path in results["directories"]:
            try:
                if full_path.exists():
                    shutil.rmtree(full_path)
                    self.deleted_items.append(str(full_path))
                    print(f"  ✓ Deleted: {path}/")
            except Exception as e:
                self.errors.append((path, str(e)))
                print(f"  ✗ Error deleting {path}: {e}")
        
        # Summary
        print(f"\n📊 CLEANUP COMPLETE")
        print(f"  • Deleted: {len(self.deleted_items)} items")
        print(f"  • Errors: {len(self.errors)}")
    
    def create_rollback_script(self, manifest_file: Path) -> None:
        """Create a rollback script to restore deleted files."""
        if self.dry_run:
            return
            
        rollback_file = manifest_file.parent / f"rollback_{manifest_file.stem}.py"
        
        rollback_content = f'''#!/usr/bin/env python3
"""
Rollback script for cleanup performed on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
This script helps identify what was deleted. Manual restoration from backup/git is required.
"""

import json
from pathlib import Path

manifest_file = "{manifest_file.name}"
manifest_path = Path(__file__).parent / manifest_file

print("CLEANUP ROLLBACK INFORMATION")
print("=" * 80)

try:
    with open(manifest_path) as f:
        data = json.load(f)
    
    print(f"Cleanup performed on: {{data['timestamp']}}")
    print(f"Base directory: {{data['base_dir']}}")
    print()
    
    print("DELETED DIRECTORIES:")
    for d in data['directories']:
        print(f"  • {{d}}")
    
    print("\\nDELETED FILES:")
    for f in data['files']:
        print(f"  • {{f}}")
    
    print("\\nTO RESTORE:")
    print("1. Check out the files from git:")
    print("   git checkout HEAD~ -- <path>")
    print("2. Or restore from your backup")
    
except Exception as e:
    print(f"Error reading manifest: {{e}}")
'''
        
        with open(rollback_file, "w") as f:
            f.write(rollback_content)
        
        rollback_file.chmod(0o755)
        print(f"✅ Rollback script created: {rollback_file}")


def main():
    """Main cleanup function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up redundant files after AgentiCraft refactoring"
    )
    parser.add_argument(
        "--execute", 
        action="store_true",
        help="Actually delete files (default is dry run)"
    )
    parser.add_argument(
        "--skip-review",
        action="store_true", 
        help="Skip showing files that need review"
    )
    
    args = parser.parse_args()
    
    cleanup = CleanupManager(BASE_DIR, dry_run=not args.execute)
    
    print("🔍 Scanning for redundant files...")
    results = cleanup.scan_redundant_files()
    
    if not args.skip_review:
        cleanup.show_summary(results)
    
    # Check if there's anything to delete
    if not results["directories"] and not results["files"]:
        print("\n✨ No redundant files found! Cleanup may have already been performed.")
        return
    
    # Ask for confirmation
    if args.execute:
        print("\n⚠️  WARNING: This will permanently delete files!")
        print("Make sure you have committed all changes to git.")
        response = input("\nProceed with deletion? (type 'yes' to confirm): ")
        
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled.")
            return
    
    # Create backup manifest
    manifest_file = cleanup.create_backup_manifest(results)
    
    # Delete files
    cleanup.delete_items(results)
    
    # Create rollback script
    cleanup.create_rollback_script(manifest_file)
    
    if not args.execute:
        print("\n💡 To actually delete files, run with --execute flag:")
        print(f"   python {Path(__file__).name} --execute")


if __name__ == "__main__":
    main()
