#!/usr/bin/env python3
"""Minimal test to reproduce the exact error."""

import sys

# Clear all agenticraft imports
for k in list(sys.modules.keys()):
    if k.startswith('agenticraft'):
        del sys.modules[k]

print("Minimal import error reproduction test")
print("=" * 60)

# Test the exact failing case from the original error
print("\nTest case: from agenticraft.core import reasoning")
try:
    # This is what seems to fail
    from agenticraft.core import reasoning
    print("✅ Success! No error occurred.")
    print(f"   reasoning module: {reasoning}")
    print(f"   __all__ = {getattr(reasoning, '__all__', 'Not defined')}")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    
    # Let's see if we can understand the error better
    error_str = str(e)
    print(f"\nError string: '{error_str}'")
    
    # Try to understand where this is coming from
    if "ThoughtProcess" in error_str:
        print("\n⚠️  The error mentions ThoughtProcess!")
        print("This means something is trying to import ThoughtProcess")
        
        # Let's trace back
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Check the exception details
        print(f"\nException type: {type(e)}")
        print(f"Exception args: {e.args}")
        
        # ImportError has special attributes
        if hasattr(e, 'name'):
            print(f"Import name: {e.name}")
        if hasattr(e, 'path'):  
            print(f"Import path: {e.path}")

# Let's also test if this works
print("\n" + "-" * 60)
print("Alternative test: import agenticraft.core.reasoning")
try:
    import agenticraft.core.reasoning
    print("✅ Direct import works!")
except ImportError as e:
    print(f"❌ Direct import also fails: {e}")

# One more test
print("\n" + "-" * 60)
print("Test: from agenticraft import Agent")
try:
    from agenticraft import Agent
    print("✅ Agent import works!")
except ImportError as e:
    print(f"❌ Agent import fails: {e}")
