#!/usr/bin/env python3
"""
Import update script for AgentiCraft refactoring
Updates all imports from redundant modules to their new locations
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Define import mappings
IMPORT_MAPPINGS = {
    # Transport mappings
    r'from\s+agenticraft\.protocols\.mcp\.transport': 'from agenticraft.core.transport',
    r'import\s+agenticraft\.protocols\.mcp\.transport': 'import agenticraft.core.transport',
    
    # Auth mappings
    r'from\s+agenticraft\.protocols\.mcp\.auth': 'from agenticraft.core.auth',
    r'import\s+agenticraft\.protocols\.mcp\.auth': 'import agenticraft.core.auth',
    r'from\s+agenticraft\.security\.auth': 'from agenticraft.core.auth',
    r'import\s+agenticraft\.security\.auth': 'import agenticraft.core.auth',
    r'from\s+agenticraft\.security\.authentication': 'from agenticraft.core.auth',
    r'import\s+agenticraft\.security\.authentication': 'import agenticraft.core.auth',
    r'from\s+agenticraft\.security\.authorization': 'from agenticraft.core.auth',
    r'import\s+agenticraft\.security\.authorization': 'import agenticraft.core.auth',
    
    # Config mappings
    r'from\s+agenticraft\.utils\.config': 'from agenticraft.core.config',
    r'import\s+agenticraft\.utils\.config': 'import agenticraft.core.config',
    
    # Fabric mappings
    r'from\s+agenticraft\.fabric\.unified\s+import': 'from agenticraft.fabric.agent import',
    r'from\s+agenticraft\.fabric\.unified': 'from agenticraft.fabric.agent',
    r'import\s+agenticraft\.fabric\.unified': 'import agenticraft.fabric.agent',
    
    # Enhanced fabric mappings (needs careful handling)
    r'from\s+agenticraft\.fabric\.unified_enhanced': 'from agenticraft.fabric.agent',
    r'import\s+agenticraft\.fabric\.unified_enhanced': 'import agenticraft.fabric.agent',
}

# Files to exclude from processing
EXCLUDE_PATTERNS = [
    '*.pyc',
    '__pycache__',
    'venv/',
    '.git/',
    'build/',
    'dist/',
    '*.egg-info/',
    'refactoring_tools/'
]

class ImportUpdater:
    def __init__(self, root_path: str, dry_run: bool = True):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.changes = []
        self.errors = []
        
    def should_process_file(self, filepath: Path) -> bool:
        """Check if file should be processed"""
        str_path = str(filepath)
        
        # Check exclude patterns
        for pattern in EXCLUDE_PATTERNS:
            if pattern in str_path:
                return False
                
        # Only process Python files
        return filepath.suffix == '.py'
        
    def update_imports_in_file(self, filepath: Path) -> List[Tuple[str, str, int]]:
        """Update imports in a single file"""
        changes = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
                
            # Apply all import mappings
            for pattern, replacement in IMPORT_MAPPINGS.items():
                # Count occurrences before replacement
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    changes.append((pattern, replacement, len(matches)))
                    
            # If changes were made, write the file
            if content != original_content:
                if not self.dry_run:
                    # Create backup
                    backup_path = filepath.with_suffix('.py.backup')
                    shutil.copy2(filepath, backup_path)
                    
                    # Write updated content
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                self.changes.append((filepath, changes))
                
        except Exception as e:
            self.errors.append((filepath, str(e)))
            
        return changes
        
    def process_directory(self):
        """Process all Python files in the directory tree"""
        print(f"Processing directory: {self.root_path}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        print("-" * 60)
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern.rstrip('/') == d for pattern in EXCLUDE_PATTERNS if pattern.endswith('/'))]
            
            for file in files:
                filepath = root_path / file
                if self.should_process_file(filepath):
                    python_files.append(filepath)
                    
        print(f"Found {len(python_files)} Python files to process\n")
        
        # Process each file
        for filepath in python_files:
            changes = self.update_imports_in_file(filepath)
            if changes:
                print(f"\n{filepath.relative_to(self.root_path)}:")
                for pattern, replacement, count in changes:
                    print(f"  - {count} occurrence(s) of '{pattern}' -> '{replacement}'")
                    
    def generate_report(self):
        """Generate a summary report"""
        print("\n" + "=" * 60)
        print("SUMMARY REPORT")
        print("=" * 60)
        
        print(f"\nTotal files modified: {len(self.changes)}")
        
        if self.changes:
            print("\nFiles with changes:")
            for filepath, changes in self.changes:
                total_changes = sum(count for _, _, count in changes)
                print(f"  - {filepath.relative_to(self.root_path)}: {total_changes} changes")
                
        if self.errors:
            print(f"\nErrors encountered: {len(self.errors)}")
            for filepath, error in self.errors:
                print(f"  - {filepath.relative_to(self.root_path)}: {error}")
                
        if self.dry_run:
            print("\n⚠️  This was a DRY RUN. No files were actually modified.")
            print("To apply changes, run with --apply flag")
            
    def verify_new_modules_exist(self):
        """Verify that target modules exist"""
        print("\nVerifying target modules exist...")
        
        required_modules = [
            'agenticraft/core/transport',
            'agenticraft/core/auth',
            'agenticraft/core/config',
            'agenticraft/fabric/agent'
        ]
        
        missing = []
        for module in required_modules:
            module_path = self.root_path / module
            if not (module_path.with_suffix('.py').exists() or module_path.is_dir()):
                missing.append(module)
                
        if missing:
            print("⚠️  WARNING: The following target modules don't exist:")
            for module in missing:
                print(f"    - {module}")
            print("\nMake sure these modules are created before running the update!")
            return False
            
        print("✓ All target modules exist")
        return True

def main():
    parser = argparse.ArgumentParser(description='Update imports for AgentiCraft refactoring')
    parser.add_argument('--apply', action='store_true', 
                       help='Apply changes (default is dry-run)')
    parser.add_argument('--path', default='/Users/zahere/Desktop/TLV/agenticraft',
                       help='Path to AgentiCraft root directory')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify that target modules exist')
    
    args = parser.parse_args()
    
    updater = ImportUpdater(args.path, dry_run=not args.apply)
    
    if args.verify_only:
        updater.verify_new_modules_exist()
        return
        
    # First verify modules exist
    if not updater.verify_new_modules_exist():
        print("\n❌ Cannot proceed without target modules")
        return
        
    # Process files
    updater.process_directory()
    updater.generate_report()

if __name__ == '__main__':
    main()
