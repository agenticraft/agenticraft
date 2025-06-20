#!/usr/bin/env python3
"""
Quick import diagnostics - focuses only on agenticraft package.
Much faster than full scan by excluding venv, tests, etc.
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict

def quick_check():
    """Run quick import diagnostics on core modules only."""
    
    base_path = Path.cwd() / 'agenticraft'
    if not base_path.exists():
        print("❌ Error: agenticraft directory not found")
        return 1
        
    print("🚀 Quick Import Diagnostics (core modules only)")
    print("=" * 50)
    
    # Core modules to check
    core_modules = [
        'agenticraft/__init__.py',
        'agenticraft/core/__init__.py',
        'agenticraft/core/agent.py',
        'agenticraft/core/tool.py',
        'agenticraft/core/workflow.py',
        'agenticraft/core/exceptions.py',
        'agenticraft/core/provider.py',
        'agenticraft/agents/__init__.py',
        'agenticraft/providers/__init__.py',
    ]
    
    # Check each module
    issues = defaultdict(list)
    
    for module_path in core_modules:
        full_path = Path.cwd() / module_path
        if not full_path.exists():
            issues[module_path].append("File not found")
            continue
            
        # Try to import
        module_name = module_path.replace('/', '.').replace('.py', '')
        if module_name.endswith('.__init__'):
            module_name = module_name[:-9]
            
        print(f"\nChecking {module_name}...")
        
        try:
            # Parse the file
            with open(full_path, 'r') as f:
                tree = ast.parse(f.read())
                
            # Check for problematic imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Check for circular patterns
                        if 'agents' in module_name and 'core' in module_name:
                            issues[module_path].append(f"Cross-layer import: {node.module}")
                        
                        # Check for star imports
                        if any(alias.name == '*' for alias in node.names):
                            issues[module_path].append(f"Star import from {node.module}")
                            
            # Try actual import
            try:
                __import__(module_name)
                print(f"  ✅ Imports successfully")
            except ImportError as e:
                issues[module_path].append(f"Import failed: {e}")
                print(f"  ❌ Import failed: {e}")
                
        except SyntaxError as e:
            issues[module_path].append(f"Syntax error: {e}")
            print(f"  ❌ Syntax error: {e}")
        except Exception as e:
            issues[module_path].append(f"Error: {e}")
            print(f"  ❌ Error: {e}")
            
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if not issues:
        print("✅ All core modules import successfully!")
    else:
        print(f"❌ Found issues in {len(issues)} modules:\n")
        for module, problems in issues.items():
            print(f"{module}:")
            for problem in problems:
                print(f"  - {problem}")
                
    # Quick circular dependency check
    print("\nQuick circular dependency check...")
    
    # Check most common circular patterns
    patterns = [
        ('agenticraft.core.agent', 'agenticraft.agents'),
        ('agenticraft.core.tool', 'agenticraft.tools'),
        ('agenticraft.core.provider', 'agenticraft.providers'),
    ]
    
    for mod1, mod2 in patterns:
        try:
            # Check if mod1 imports mod2
            m1_file = Path.cwd() / mod1.replace('.', '/') + '.py'
            if m1_file.exists():
                with open(m1_file, 'r') as f:
                    if mod2 in f.read():
                        print(f"  ⚠️  Potential circular: {mod1} → {mod2}")
        except:
            pass
            
    print("\nDiagnostics complete!")
    return 0

if __name__ == "__main__":
    sys.exit(quick_check())
