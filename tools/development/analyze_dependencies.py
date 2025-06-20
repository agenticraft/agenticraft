#!/usr/bin/env python3
"""
Safe dependency checker for AgentiCraft refactoring.

This script helps identify which files are actually being used
before making any deletions.
"""

import os
import ast
import sys
from pathlib import Path
from collections import defaultdict


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to find imports."""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.imports = []
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                'type': 'import',
                'module': alias.name,
                'line': node.lineno
            })
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        module = node.module or ''
        level = node.level
        
        # Handle relative imports
        if level > 0:
            # Convert relative to absolute based on file location
            parts = self.file_path.parts
            pkg_index = parts.index('agenticraft') if 'agenticraft' in parts else -1
            if pkg_index >= 0:
                current_package = '.'.join(parts[pkg_index:-1])
                if level == 1:
                    base = current_package
                else:
                    base_parts = current_package.split('.')
                    base = '.'.join(base_parts[:-(level-1)])
                module = f"{base}.{module}" if module else base
        
        for alias in node.names:
            self.imports.append({
                'type': 'from',
                'module': module,
                'name': alias.name,
                'line': node.lineno
            })
        self.generic_visit(node)


def find_imports_in_file(file_path):
    """Find all imports in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            
        visitor = ImportVisitor(file_path)
        visitor.visit(tree)
        return visitor.imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []


def analyze_module_usage(base_path):
    """Analyze which modules are being imported across the codebase."""
    # Module -> List of (file, line) where it's imported
    module_imports = defaultdict(list)
    
    # Scan all Python files
    for py_file in Path(base_path).rglob("*.py"):
        # Skip test files and examples for now
        if any(skip in str(py_file) for skip in ['test_', '__pycache__', 'backup']):
            continue
            
        imports = find_imports_in_file(py_file)
        
        for imp in imports:
            module = imp['module']
            if module.startswith('agenticraft'):
                module_imports[module].append({
                    'file': py_file,
                    'line': imp['line'],
                    'type': imp['type'],
                    'name': imp.get('name', '*')
                })
    
    return module_imports


def check_module_exists(base_path, module_path):
    """Check if a module actually exists."""
    # Convert module path to file path
    parts = module_path.split('.')
    
    # Try as package (__init__.py)
    package_path = base_path / Path(*parts) / '__init__.py'
    if package_path.exists():
        return True, 'package'
        
    # Try as module (.py file)
    module_file = base_path / Path(*parts[:-1]) / f"{parts[-1]}.py"
    if module_file.exists():
        return True, 'module'
        
    return False, None


def analyze_potentially_redundant(base_path):
    """Analyze potentially redundant modules."""
    potentially_redundant = [
        # Fabric modules
        'agenticraft.fabric.unified',
        'agenticraft.fabric.unified_enhanced',
        'agenticraft.fabric.sdk_fabric',
        'agenticraft.fabric.adapters_base',
        
        # Protocol modules
        'agenticraft.protocols.mcp.transport',
        'agenticraft.protocols.mcp.auth',
        'agenticraft.protocols.a2a.centralized',
        'agenticraft.protocols.a2a.decentralized',
        'agenticraft.protocols.a2a.hybrid',
        'agenticraft.protocols.bridges',
        'agenticraft.protocols.external',
        
        # Security modules
        'agenticraft.security.authentication',
        'agenticraft.security.authorization',
        'agenticraft.security.auth',
        
        # Utils
        'agenticraft.utils.config',
    ]
    
    module_imports = analyze_module_usage(base_path)
    
    print("Analysis of Potentially Redundant Modules")
    print("=" * 60)
    
    for module in potentially_redundant:
        print(f"\n{module}:")
        
        # Check if module exists
        exists, mod_type = check_module_exists(base_path, module)
        if not exists:
            print("  ✗ Module doesn't exist (already deleted?)")
            continue
            
        print(f"  ✓ Exists as {mod_type}")
        
        # Find imports
        imports = []
        for key in module_imports:
            if key == module or key.startswith(module + '.'):
                imports.extend(module_imports[key])
        
        if imports:
            print(f"  ⚠️  Imported {len(imports)} times:")
            # Show first 5 imports
            for imp in imports[:5]:
                rel_path = imp['file'].relative_to(base_path)
                print(f"    - {rel_path}:{imp['line']} ({imp['type']} {imp['name']})")
            if len(imports) > 5:
                print(f"    ... and {len(imports) - 5} more")
        else:
            print("  ✓ No imports found (possibly safe to delete)")


def find_cross_references(base_path):
    """Find which modules reference each other."""
    print("\n\nCross-Reference Analysis")
    print("=" * 60)
    
    # Key modules to check
    key_modules = {
        'core.transport': 'protocols.mcp.transport',
        'core.auth': 'protocols.mcp.auth',
        'core.patterns': 'agents.patterns',
        'fabric.agent': 'fabric.unified',
    }
    
    module_imports = analyze_module_usage(base_path)
    
    for new_module, old_module in key_modules.items():
        new_full = f"agenticraft.{new_module}"
        old_full = f"agenticraft.{old_module}"
        
        print(f"\n{new_module} vs {old_module}:")
        
        # Who imports the new module?
        new_importers = module_imports.get(new_full, [])
        print(f"  New module imported by: {len(new_importers)} files")
        
        # Who imports the old module?
        old_importers = [imp for key, imps in module_imports.items() 
                        for imp in imps if key.startswith(old_full)]
        print(f"  Old module imported by: {len(old_importers)} files")
        
        # Any files importing both?
        new_files = {str(imp['file']) for imp in new_importers}
        old_files = {str(imp['file']) for imp in old_importers}
        both = new_files & old_files
        if both:
            print(f"  ⚠️  {len(both)} files import BOTH modules!")


def main():
    base_path = Path.cwd()
    
    # Verify we're in the right directory
    if not (base_path / "agenticraft").exists():
        print("Error: 'agenticraft' directory not found.")
        print("Please run this script from the AgentiCraft project root.")
        return 1
    
    print("AgentiCraft Dependency Analysis")
    print("This will help identify what's safe to delete\n")
    
    # Analyze potentially redundant modules
    analyze_potentially_redundant(base_path)
    
    # Find cross-references
    find_cross_references(base_path)
    
    print("\n\nSummary:")
    print("- ✓ Modules with no imports are likely safe to delete")
    print("- ⚠️  Modules with imports need careful review")
    print("- Check if importing files have been updated to use new modules")
    print("- Always backup before deleting!")
    
    return 0


if __name__ == "__main__":
    exit(main())
