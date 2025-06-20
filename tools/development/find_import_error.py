#!/usr/bin/env python3
"""Find where ThoughtProcess is being imported."""

import ast
import os

def find_imports_in_file(filepath):
    """Find all imports in a Python file using AST."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and 'reasoning' in node.module:
                    for alias in node.names:
                        imports.append({
                            'line': node.lineno,
                            'module': node.module,
                            'name': alias.name,
                            'as': alias.asname
                        })
        return imports
    except Exception as e:
        return []

def search_all_files(root_dir):
    """Search all Python files for reasoning imports."""
    exclude_dirs = {'.git', '__pycache__', 'venv', 'site', 'dist', '.pytest_cache', 'tests'}
    
    found_issues = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                imports = find_imports_in_file(filepath)
                
                for imp in imports:
                    if imp['name'] == 'ThoughtProcess' or imp['name'] == '*':
                        rel_path = os.path.relpath(filepath, root_dir)
                        found_issues.append({
                            'file': rel_path,
                            'line': imp['line'],
                            'import': imp
                        })
    
    return found_issues

print("Searching for ThoughtProcess imports using AST...")
print("=" * 60)

agenticraft_dir = "/Users/zahere/Desktop/TLV/agenticraft"
issues = search_all_files(agenticraft_dir)

if issues:
    print(f"\n🔍 Found {len(issues)} problematic imports:\n")
    for issue in issues:
        print(f"📄 {issue['file']}")
        print(f"   Line {issue['line']}: from {issue['import']['module']} import {issue['import']['name']}")
        if issue['import']['as']:
            print(f"   Imported as: {issue['import']['as']}")
else:
    print("\n✅ No problematic imports found!")

# Also check __init__.py files
print("\n" + "=" * 60)
print("Checking __init__.py files for star imports...")

init_files = []
for dirpath, dirnames, filenames in os.walk(agenticraft_dir):
    if '__init__.py' in filenames and '__pycache__' not in dirpath:
        init_path = os.path.join(dirpath, '__init__.py')
        rel_path = os.path.relpath(init_path, agenticraft_dir)
        init_files.append(rel_path)

print(f"\nFound {len(init_files)} __init__.py files")
for init_file in sorted(init_files)[:10]:  # Show first 10
    print(f"  - {init_file}")
