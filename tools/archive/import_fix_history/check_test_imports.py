#!/usr/bin/env python3
"""
Check for potential import issues in tests after refactoring.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def find_imports_in_file(filepath):
    """Extract all agenticraft imports from a file."""
    imports = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Find all import statements
        import_patterns = [
            r'from\s+agenticraft\.([^\s]+)\s+import\s+([^\n]+)',
            r'import\s+agenticraft\.([^\s]+)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    module = match[0]
                    items = match[1] if len(match) > 1 else ""
                else:
                    module = match
                    items = ""
                imports.append((module, items))
                
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return imports

def check_module_exists(module_path, root_path):
    """Check if a module exists in the codebase."""
    # Convert module path to file path
    parts = module_path.split('.')
    
    # Check as a module file
    file_path = root_path / 'agenticraft' / '/'.join(parts) / '__init__.py'
    if file_path.exists():
        return True
        
    # Check as a python file
    file_path = root_path / 'agenticraft' / '/'.join(parts[:-1]) / f"{parts[-1]}.py"
    if file_path.exists():
        return True
        
    # Check as a directory
    dir_path = root_path / 'agenticraft' / '/'.join(parts)
    if dir_path.exists() and dir_path.is_dir():
        return True
        
    return False

def main():
    root_path = Path('/Users/zahere/Desktop/TLV/agenticraft')
    test_path = root_path / 'tests'
    
    # Track all imports
    all_imports = defaultdict(list)
    missing_modules = defaultdict(list)
    
    # Scan all test files
    for root, dirs, files in os.walk(test_path):
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                imports = find_imports_in_file(filepath)
                
                for module, items in imports:
                    all_imports[module].append({
                        'file': str(filepath.relative_to(root_path)),
                        'items': items
                    })
                    
                    # Check if module exists
                    if not check_module_exists(module, root_path):
                        missing_modules[module].append(str(filepath.relative_to(root_path)))
    
    # Report findings
    print("=" * 80)
    print("AgentiCraft Test Import Analysis")
    print("=" * 80)
    
    # Most imported modules
    print("\n## Most Imported Modules in Tests")
    sorted_imports = sorted(all_imports.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for module, imports in sorted_imports:
        print(f"  {module}: {len(imports)} imports")
    
    # Missing modules
    if missing_modules:
        print("\n## Potentially Missing Modules")
        for module, files in missing_modules.items():
            print(f"\n  {module}:")
            for file in files[:3]:  # Show first 3 files
                print(f"    - {file}")
            if len(files) > 3:
                print(f"    ... and {len(files) - 3} more files")
    else:
        print("\n✓ All imported modules appear to exist")
    
    # Check for old module patterns
    print("\n## Checking for Old Module Patterns")
    old_patterns = {
        'fabric.unified': 'Should now use fabric.agent',
        'security.auth': 'Should now use core.auth',
        'utils.config': 'Should now use core.config',
        'protocols.mcp.auth': 'Should now use core.auth',
        'protocols.mcp.transport': 'Should now use core.transport'
    }
    
    for old_module, suggestion in old_patterns.items():
        if old_module in all_imports:
            print(f"\n  ⚠️  Found imports of '{old_module}'")
            print(f"     Suggestion: {suggestion}")
            print(f"     Used in {len(all_imports[old_module])} files")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"  Total unique module imports: {len(all_imports)}")
    print(f"  Potentially missing modules: {len(missing_modules)}")
    print("=" * 80)

if __name__ == '__main__':
    main()
