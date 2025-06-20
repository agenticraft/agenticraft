#!/usr/bin/env python3
"""
Quick refactoring status check
Shows current state of the refactoring process
"""

import os
from pathlib import Path
from datetime import datetime

def check_status():
    root_path = Path('/Users/zahere/Desktop/TLV/agenticraft')
    
    print("AgentiCraft Refactoring Status")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project: {root_path}\n")
    
    # Check for backup directories
    backup_dir = root_path / 'refactoring_backup'
    if backup_dir.exists():
        backups = list(backup_dir.iterdir())
        print(f"📁 Backups found: {len(backups)}")
        for backup in backups:
            print(f"   - {backup.name}")
    else:
        print("📁 No backups found")
        
    print()
    
    # Check if redundant modules still exist
    redundant_modules = [
        'fabric/unified.py',
        'fabric/unified_enhanced.py', 
        'fabric/sdk_fabric.py',
        'fabric/adapters_base.py',
        'protocols/mcp/transport',
        'protocols/mcp/auth',
        'security/auth.py',
        'utils/config.py'
    ]
    
    still_exists = []
    deleted = []
    
    for module in redundant_modules:
        full_path = root_path / 'agenticraft' / module
        if full_path.exists():
            still_exists.append(module)
        else:
            deleted.append(module)
            
    print(f"🗑️  Redundant modules deleted: {len(deleted)}/{len(redundant_modules)}")
    if deleted:
        print("   Deleted:")
        for module in deleted:
            print(f"   ✓ {module}")
            
    if still_exists:
        print("\n   Still exists:")
        for module in still_exists:
            print(f"   ✗ {module}")
            
    print()
    
    # Check if new modules exist
    new_modules = [
        'core/transport',
        'core/auth',
        'core/config',
        'fabric/agent'
    ]
    
    print("✨ New module structure:")
    for module in new_modules:
        full_path = root_path / 'agenticraft' / module
        exists = full_path.exists() or full_path.with_suffix('.py').exists()
        status = "✓" if exists else "✗"
        print(f"   {status} agenticraft/{module}")
        
    print()
    
    # Check for backup files
    backup_files = list(root_path.rglob("*.py.backup"))
    if backup_files:
        print(f"💾 Found {len(backup_files)} .backup files from import updates")
        print("   (These can be deleted after confirming everything works)")
        
    # Check for migration report
    migration_report = root_path / 'refactoring_tools' / 'migration_needed.txt'
    if migration_report.exists():
        print(f"\n📄 Migration report available at: refactoring_tools/migration_needed.txt")
        
    print("\n" + "=" * 60)
    print("\nNext steps:")
    
    if still_exists:
        print("1. Run: python refactoring_tools/update_imports.py --apply")
        print("2. Run: python refactoring_tools/delete_redundant_modules.py --execute")
    else:
        print("✅ Refactoring appears to be complete!")
        print("   Run: python refactoring_tools/validate_refactoring.py --post-refactor")
        print("   to validate everything is working correctly.")

if __name__ == '__main__':
    check_status()
