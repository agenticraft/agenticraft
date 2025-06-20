#!/usr/bin/env python3
"""Debug the exact import error location."""

import sys
import importlib

print("Debugging import error for 'ThoughtProcess'...")
print("=" * 60)

# Step 1: Try importing the module with detailed error info
print("\n1. Attempting to import agenticraft.core.reasoning:")
try:
    # First clear any cached imports
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith('agenticraft')]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    import agenticraft.core.reasoning
    print("✅ Module imported successfully")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    print(f"   Error args: {e.args}")
    
    # Try to get more info
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

# Step 2: Check what's in __all__ if module exists
print("\n2. Checking module contents:")
try:
    import agenticraft.core.reasoning as reasoning
    if hasattr(reasoning, '__all__'):
        print(f"__all__ = {reasoning.__all__}")
        
        # Check if all items in __all__ exist
        for item in reasoning.__all__:
            if hasattr(reasoning, item):
                print(f"  ✅ {item} exists")
            else:
                print(f"  ❌ {item} is in __all__ but doesn't exist!")
except Exception as e:
    print(f"Could not check module contents: {e}")

# Step 3: Try to trace where the error originates
print("\n3. Import chain analysis:")
print("Checking which module is trying to import ThoughtProcess...")

# Check if it's coming from a property or __getattr__
try:
    # Import just the module path
    import agenticraft.core
    print("✅ agenticraft.core imported")
    
    # Check if core.__init__ has any issues
    if hasattr(agenticraft.core, '__all__'):
        print(f"   core.__all__ = {agenticraft.core.__all__}")
except Exception as e:
    print(f"❌ Error importing agenticraft.core: {e}")
