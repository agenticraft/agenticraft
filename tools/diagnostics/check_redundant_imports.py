#!/usr/bin/env python3
"""
Check for imports of redundant modules before deletion.

This script scans the codebase for any imports of modules
that are marked for deletion.
"""

import os
import re
from pathlib import Path


# Modules that will be deleted
REDUNDANT_MODULES = [
    # MCP redundant modules
    "agenticraft.protocols.mcp.transport",
    "agenticraft.protocols.mcp.auth",
    "agenticraft.protocols.mcp.decorators",
    
    # A2A redundant modules
    "agenticraft.protocols.a2a.centralized",
    "agenticraft.protocols.a2a.decentralized", 
    "agenticraft.protocols.a2a.hybrid",
    
    # Security redundant modules
    "agenticraft.security.authentication",
    "agenticraft.security.authorization",
    "agenticraft.security.auth",
    
    # Fabric redundant modules
    "agenticraft.fabric.adapters",
    "agenticraft.fabric.unified",
    "agenticraft.fabric.unified_enhanced",
    "agenticraft.fabric.sdk_fabric",
    "agenticraft.fabric.adapters_base",
    
    # Utils redundant
    "agenticraft.utils.config",
    
    # Protocol bridges/external
    "agenticraft.protocols.bridges",
    "agenticraft.protocols.external",
]


def find_imports(file_path: Path) -> list[tuple[int, str, str]]:
    """Find imports of redundant modules in a file."""
    imports_found = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_no, line in enumerate(lines, 1):
            # Check for 'import' statements
            for module in REDUNDANT_MODULES:
                # Pattern 1: from module import ...
                if f"from {module}" in line:
                    imports_found.append((line_no, line.strip(), module))
                    
                # Pattern 2: import module
                if re.search(rf"\bimport\s+{re.escape(module)}\b", line):
                    imports_found.append((line_no, line.strip(), module))
                    
                # Pattern 3: Relative imports that might reference these
                module_parts = module.split('.')
                if len(module_parts) > 2:
                    relative_import = module_parts[-1]
                    if f"from .{relative_import}" in line:
                        # Check if this is in the right directory
                        parent_module = '.'.join(module_parts[:-1])
                        file_module = str(file_path).replace('/', '.').replace('\\', '.')
                        if parent_module in file_module:
                            imports_found.append((line_no, line.strip(), module))
                            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return imports_found


def scan_codebase(base_path: Path):
    """Scan the entire codebase for imports of redundant modules."""
    all_imports = {}
    
    # Directories to skip
    SKIP_DIRS = {
        'venv', '.venv', 'env', '.env',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        '.git', '.github', 'node_modules',
        'build', 'dist', 'egg-info', '.egg-info',
        'htmlcov', '.coverage', 'site',
        'docs/_build', 'exported_code',
        '.cleanup_temp', 'backup', 'backups',
        'backup_before_cleanup'
    }
    
    # Scan Python files
    for py_file in base_path.rglob("*.py"):
        # Skip excluded directories
        if any(skip_dir in py_file.parts for skip_dir in SKIP_DIRS):
            continue
            
        # Skip the cleanup scripts themselves
        if py_file.name in ["cleanup_redundant.py", "check_redundant_imports.py"]:
            continue
            
        imports = find_imports(py_file)
        if imports:
            all_imports[py_file] = imports
            
    return all_imports


def main():
    base_path = Path.cwd()
    
    # Verify we're in the right directory
    if not (base_path / "agenticraft").exists():
        print("Error: 'agenticraft' directory not found.")
        print("Please run this script from the AgentiCraft project root.")
        return 1
        
    print("Scanning for imports of redundant modules...")
    print()
    
    all_imports = scan_codebase(base_path)
    
    if not all_imports:
        print("✓ No imports of redundant modules found!")
        print("It's safe to proceed with deletion.")
    else:
        print("⚠️  Found imports of redundant modules:")
        print()
        
        # Group by module
        by_module = {}
        for file_path, imports in all_imports.items():
            for line_no, line, module in imports:
                if module not in by_module:
                    by_module[module] = []
                by_module[module].append((file_path, line_no, line))
        
        # Display results
        for module in sorted(by_module.keys()):
            print(f"\n{module}:")
            for file_path, line_no, line in by_module[module]:
                rel_path = file_path.relative_to(base_path)
                print(f"  {rel_path}:{line_no} - {line}")
                
        print(f"\n⚠️  Found {sum(len(imports) for imports in all_imports.values())} imports in {len(all_imports)} files")
        print("\nThese imports need to be updated before deleting the redundant files.")
        print("\nSuggested replacements:")
        print("  - agenticraft.protocols.mcp.transport.* → agenticraft.core.transport.*")
        print("  - agenticraft.protocols.mcp.auth.* → agenticraft.core.auth.*")
        print("  - agenticraft.security.auth → agenticraft.core.auth")
        print("  - agenticraft.utils.config → agenticraft.core.config")
        print("  - agenticraft.fabric.unified → agenticraft.fabric.agent")
        
    return 0


if __name__ == "__main__":
    exit(main())
