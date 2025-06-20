#!/usr/bin/env python3
"""
Fix redundant imports in AgentiCraft codebase.
This script updates imports from redundant modules to their correct locations.
"""

import os
import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    # Fabric adapters - these exist, no need to change
    # "from agenticraft.fabric.adapters": "from agenticraft.fabric.adapters",
    
    # Protocol imports that need updating
    "from agenticraft.protocols.a2a": "from agenticraft.protocols.a2a",
    "from .task_router": "from .task_router",
    "from .": "from .",
    
    "from agenticraft.protocols.a2a": "from agenticraft.protocols.a2a",
    "from .consensus": "from .consensus",
    "from .": "from .",
    
    "from agenticraft.protocols.a2a": "from agenticraft.protocols.a2a",
    "from .mesh_network": "from .mesh_network",
    "from .": "from .",
    
    "from agenticraft.protocols": "from agenticraft.protocols",
    "from agenticraft.core.transport": "from agenticraft.core.transport",
    
    # Auth imports
    "from agenticraft.core.auth": "from agenticraft.core.auth",
    "from agenticraft.core.authorization": "from agenticraft.core.auth",
    "from agenticraft.core.auth": "from agenticraft.core.auth",
}

def update_imports_in_file(file_path: Path) -> int:
    """Update imports in a single file."""
    changes_made = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply each mapping
        for old_import, new_import in IMPORT_MAPPINGS.items():
            # Count occurrences before replacement
            occurrences = content.count(old_import)
            if occurrences > 0:
                content = content.replace(old_import, new_import)
                changes_made += occurrences
                print(f"  Updated {occurrences} occurrences of '{old_import}'")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated {file_path.name}")
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
    
    return changes_made

def main():
    """Main function to fix all redundant imports."""
    base_path = Path.cwd()
    
    # Verify we're in the right directory
    if not (base_path / "agenticraft").exists():
        print("Error: 'agenticraft' directory not found.")
        print("Please run this script from the AgentiCraft project root.")
        return 1
    
    print("🔧 Fixing Redundant Imports")
    print("=" * 50)
    
    # Directories to skip
    SKIP_DIRS = {
        'venv', '.venv', 'env', '.env',
        '__pycache__', '.pytest_cache',
        '.git', 'node_modules',
        'build', 'dist', 'site',
        'backup', 'backups'
    }
    
    total_changes = 0
    files_updated = 0
    
    # Find all Python files
    for py_file in base_path.rglob("*.py"):
        # Skip excluded directories
        if any(skip_dir in py_file.parts for skip_dir in SKIP_DIRS):
            continue
        
        # Process file
        changes = update_imports_in_file(py_file)
        if changes > 0:
            total_changes += changes
            files_updated += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Complete! Updated {total_changes} imports in {files_updated} files.")
    
    # Check which modules might need to be moved
    print("\n📋 Next Steps:")
    print("1. Move A2A protocol modules to correct locations:")
    print("   - protocols/a2a/centralized/* → protocols/a2a/")
    print("   - protocols/a2a/decentralized/* → protocols/a2a/")
    print("   - protocols/a2a/hybrid/* → protocols/a2a/")
    print("\n2. Ensure transport module exists in core/")
    print("\n3. Run tests to verify everything works")
    
    return 0

if __name__ == "__main__":
    exit(main())
