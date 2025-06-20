#!/usr/bin/env python3
"""Minimal test to isolate the import error."""

import sys
import importlib

# First, let's see what happens when we import core.reasoning module directly
print("Step 1: Import core.reasoning module directly")
try:
    spec = importlib.util.find_spec("agenticraft.core.reasoning")
    if spec:
        print(f"✅ Module found at: {spec.origin}")
        module = importlib.import_module("agenticraft.core.reasoning")
        print(f"✅ Module imported successfully")
        attrs = [x for x in dir(module) if not x.startswith('_')]
        print(f"   Available attributes: {attrs}")
        
        # Check if ThoughtProcess is in __all__
        if hasattr(module, '__all__'):
            print(f"   __all__ = {module.__all__}")
    else:
        print("❌ Module spec not found")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 2: Check what happens with 'from agenticraft import Agent'")
try:
    # Clear any cached imports
    if 'agenticraft' in sys.modules:
        del sys.modules['agenticraft']
    if 'agenticraft.core' in sys.modules:
        del sys.modules['agenticraft.core'] 
    if 'agenticraft.core.agent' in sys.modules:
        del sys.modules['agenticraft.core.agent']
    
    from agenticraft import Agent
    print("✅ Successfully imported Agent")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
