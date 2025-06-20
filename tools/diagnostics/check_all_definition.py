#!/usr/bin/env python3
"""Check if __all__ is causing the issue."""

import sys

# Clear imports
for key in list(sys.modules.keys()):
    if key.startswith('agenticraft'):
        del sys.modules[key]

print("Testing if __all__ is causing the import error...")
print("=" * 60)

# First, let's manually check what happens
print("\n1. Manually checking reasoning.py __all__:")
try:
    # Read the file content
    with open('/Users/zahere/Desktop/TLV/agenticraft/agenticraft/core/reasoning.py', 'r') as f:
        content = f.read()
    
    # Find __all__ definition
    import ast
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    # Found __all__, check its value
                    if isinstance(node.value, ast.List):
                        all_items = [elt.s for elt in node.value.elts if isinstance(elt, ast.Str)]
                        print(f"   __all__ contains: {all_items}")
                        
                        # Check if ThoughtProcess is in __all__
                        if 'ThoughtProcess' in all_items:
                            print("   ⚠️  WARNING: ThoughtProcess is in __all__!")
                        else:
                            print("   ✅ ThoughtProcess is NOT in __all__")
                        
                        # Now check if all items in __all__ are defined
                        print("\n2. Checking if all __all__ items are defined in the module:")
                        
                        # Get all class and function definitions
                        defined_names = set()
                        for node2 in ast.walk(tree):
                            if isinstance(node2, ast.ClassDef):
                                defined_names.add(node2.name)
                            elif isinstance(node2, ast.FunctionDef):
                                defined_names.add(node2.name)
                        
                        print(f"   Defined names: {defined_names}")
                        
                        # Check each item in __all__
                        for item in all_items:
                            if item in defined_names:
                                print(f"   ✅ {item} is defined")
                            else:
                                print(f"   ❌ {item} is in __all__ but NOT defined!")
                                
except Exception as e:
    print(f"Error analyzing file: {e}")
    import traceback
    traceback.print_exc()

# Now try the actual import
print("\n3. Attempting actual import:")
try:
    import agenticraft.core.reasoning
    print("✅ Import successful!")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    
    # Parse the error message
    error_msg = str(e)
    if "cannot import name" in error_msg:
        # Extract what it's trying to import
        parts = error_msg.split("'")
        if len(parts) >= 2:
            missing_name = parts[1]
            print(f"   Trying to import: '{missing_name}'")
            print(f"   From: '{parts[3] if len(parts) > 3 else 'unknown'}'")
