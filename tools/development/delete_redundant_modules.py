#!/usr/bin/env python3
"""
Safe deletion script for redundant modules
Verifies modules are no longer imported before deletion
"""

import os
import shutil
import ast
from pathlib import Path
from typing import Set, Dict, List
import argparse
from datetime import datetime

# Modules marked as redundant
REDUNDANT_MODULES = [
    'agenticraft/fabric/unified.py',
    'agenticraft/fabric/unified_enhanced.py',
    'agenticraft/fabric/sdk_fabric.py',
    'agenticraft/fabric/adapters_base.py',
    'agenticraft/protocols/mcp/transport',
    'agenticraft/protocols/mcp/auth',
    'agenticraft/protocols/a2a/centralized',
    'agenticraft/protocols/a2a/decentralized',
    'agenticraft/protocols/a2a/hybrid',
    'agenticraft/protocols/bridges',
    'agenticraft/protocols/external',
    'agenticraft/security/authentication',
    'agenticraft/security/authorization',
    'agenticraft/security/auth.py',
    'agenticraft/utils/config.py',
]

# Modules that are safe to delete (no imports found)
SAFE_TO_DELETE = [
    'agenticraft/fabric/adapters_base.py',
    'agenticraft/protocols/mcp/transport',
    'agenticraft/protocols/bridges',
    'agenticraft/security/authentication',
    'agenticraft/security/authorization',
    'agenticraft/security/auth.py',
    'agenticraft/utils/config.py',
]

class ModuleDeletionManager:
    def __init__(self, root_path: str, dry_run: bool = True):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.backup_dir = self.root_path / 'refactoring_backup' / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.imports_found = {}
        self.deletion_candidates = []
        
    def find_imports_of_module(self, module_name: str) -> Dict[str, List[str]]:
        """Find all imports of a given module"""
        imports = {}
        module_parts = module_name.replace('/', '.').replace('.py', '')
        
        for root, dirs, files in os.walk(self.root_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', 'build', 'dist']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Simple regex search for imports
                        if module_parts in content:
                            # Check for various import patterns
                            import_patterns = [
                                f'from {module_parts}',
                                f'import {module_parts}',
                                f'from {module_parts}.',
                                f'{module_parts}.',
                            ]
                            
                            found_patterns = []
                            for pattern in import_patterns:
                                if pattern in content:
                                    found_patterns.append(pattern)
                                    
                            if found_patterns:
                                imports[str(filepath.relative_to(self.root_path))] = found_patterns
                                
                    except Exception as e:
                        pass  # Skip files that can't be read
                        
        return imports
        
    def verify_module_safety(self, module_path: str) -> tuple[bool, Dict[str, List[str]]]:
        """Verify if a module is safe to delete"""
        imports = self.find_imports_of_module(module_path)
        is_safe = len(imports) == 0
        return is_safe, imports
        
    def backup_module(self, module_path: Path):
        """Create a backup of the module before deletion"""
        if not self.dry_run:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Calculate relative path for backup
            rel_path = module_path.relative_to(self.root_path)
            backup_path = self.backup_dir / rel_path
            
            # Create parent directories in backup
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file or directory
            if module_path.is_file():
                shutil.copy2(module_path, backup_path)
            else:
                shutil.copytree(module_path, backup_path)
                
            return backup_path
        return None
        
    def delete_module(self, module_path: Path) -> bool:
        """Delete a module (file or directory)"""
        try:
            if not self.dry_run:
                if module_path.is_file():
                    module_path.unlink()
                else:
                    shutil.rmtree(module_path)
            return True
        except Exception as e:
            print(f"Error deleting {module_path}: {e}")
            return False
            
    def clean_empty_directories(self):
        """Remove empty directories after deletion"""
        if self.dry_run:
            return
            
        # Walk bottom-up to remove empty directories
        for root, dirs, files in os.walk(self.root_path, topdown=False):
            root_path = Path(root)
            
            # Skip special directories
            if any(skip in str(root_path) for skip in ['venv', '.git', '__pycache__']):
                continue
                
            # Check if directory is empty (no files and no non-empty subdirs)
            if not files and not any((root_path / d).iterdir() for d in dirs if (root_path / d).exists()):
                try:
                    root_path.rmdir()
                    print(f"Removed empty directory: {root_path.relative_to(self.root_path)}")
                except:
                    pass  # Directory might not be empty due to hidden files
                    
    def analyze_modules(self):
        """Analyze all redundant modules"""
        print("Analyzing redundant modules...")
        print("=" * 60)
        
        for module in REDUNDANT_MODULES:
            module_path = self.root_path / module
            
            # Check if module exists
            if not module_path.exists():
                print(f"\n❌ {module}: Does not exist")
                continue
                
            # Check for imports
            is_safe, imports = self.verify_module_safety(module)
            
            if is_safe:
                print(f"\n✅ {module}: SAFE TO DELETE (no imports found)")
                self.deletion_candidates.append(module_path)
            else:
                print(f"\n⚠️  {module}: STILL HAS {len(imports)} IMPORTS")
                self.imports_found[module] = imports
                for file, patterns in imports.items():
                    print(f"    - {file}: {', '.join(patterns)}")
                    
    def execute_deletion(self):
        """Execute the deletion of safe modules"""
        if not self.deletion_candidates:
            print("\n❌ No modules are safe to delete")
            return
            
        print("\n" + "=" * 60)
        print(f"Ready to delete {len(self.deletion_candidates)} modules")
        print("=" * 60)
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No files will be deleted")
            print("\nWould delete:")
        else:
            print(f"\n📁 Creating backup in: {self.backup_dir.relative_to(self.root_path)}")
            print("\nDeleting:")
            
        for module_path in self.deletion_candidates:
            rel_path = module_path.relative_to(self.root_path)
            print(f"  - {rel_path}")
            
            if not self.dry_run:
                # Backup first
                backup_path = self.backup_module(module_path)
                
                # Then delete
                if self.delete_module(module_path):
                    print(f"    ✓ Deleted successfully")
                else:
                    print(f"    ✗ Deletion failed")
                    
        # Clean up empty directories
        if not self.dry_run:
            print("\nCleaning up empty directories...")
            self.clean_empty_directories()
            
    def generate_migration_report(self):
        """Generate a report of modules that still need migration"""
        if self.imports_found:
            report_path = self.root_path / 'refactoring_tools' / 'migration_needed.txt'
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                f.write("Modules Still Requiring Migration\n")
                f.write("=" * 60 + "\n\n")
                
                for module, imports in self.imports_found.items():
                    f.write(f"{module}:\n")
                    f.write(f"  Found in {len(imports)} files:\n")
                    for file, patterns in imports.items():
                        f.write(f"    - {file}\n")
                    f.write("\n")
                    
            print(f"\n📄 Migration report saved to: {report_path.relative_to(self.root_path)}")

def main():
    parser = argparse.ArgumentParser(description='Safely delete redundant AgentiCraft modules')
    parser.add_argument('--execute', action='store_true',
                       help='Execute deletion (default is analysis only)')
    parser.add_argument('--force', action='store_true',
                       help='Force deletion even if imports are found (DANGEROUS!)')
    parser.add_argument('--path', default='/Users/zahere/Desktop/TLV/agenticraft',
                       help='Path to AgentiCraft root directory')
    parser.add_argument('--quick', action='store_true',
                       help='Only process modules marked as safe')
    
    args = parser.parse_args()
    
    manager = ModuleDeletionManager(args.path, dry_run=not args.execute)
    
    # If quick mode, only process safe modules
    if args.quick:
        print("Quick mode: Only processing modules marked as safe")
        REDUNDANT_MODULES[:] = SAFE_TO_DELETE
        
    # Analyze modules
    manager.analyze_modules()
    
    # Generate migration report
    manager.generate_migration_report()
    
    # Execute deletion if requested
    if args.execute or args.force:
        if args.force and manager.imports_found:
            print("\n⚠️  WARNING: Force mode enabled. Will delete modules with active imports!")
            manager.deletion_candidates.extend(
                manager.root_path / module for module in manager.imports_found.keys()
            )
            
        manager.execute_deletion()
    else:
        print("\n💡 To delete safe modules, run with --execute flag")
        print("   To see only safe modules, run with --quick flag")

if __name__ == '__main__':
    main()
