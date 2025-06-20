#!/usr/bin/env python3
"""Clear cache and diagnose the import error."""

import os
import shutil
import sys

print("Clearing Python cache and diagnosing import issue...")
print("=" * 60)

# Clear sys.modules first
print("\n1. Clearing sys.modules...")
cleared = 0
for key in list(sys.modules.keys()):
    if 'agenticraft' in key:
        del sys.modules[key]
        cleared += 1
print(f"   Cleared {cleared} modules")

# Clear __pycache__ directories
print("\n2. Clearing __pycache__ directories...")
agenticraft_root = "/Users/zahere/Desktop/TLV/agenticraft"
for root, dirs, files in os.walk(agenticraft_root):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(pycache_path)
            print(f"   ✅ Deleted: {os.path.relpath(pycache_path, agenticraft_root)}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

# Now let's trace the import step by step
print("\n3. Step-by-step import trace:")

# Step 1: Check if we can import agenticraft
print("\n   Step 3.1: import agenticraft")
try:
    import agenticraft
    print("   ✅ Success")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Step 2: Check if we can import agenticraft.core
print("\n   Step 3.2: import agenticraft.core")
try:
    import agenticraft.core
    print("   ✅ Success")
    print(f"      __all__ = {getattr(agenticraft.core, '__all__', 'Not defined')}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Step 3: Direct import of reasoning
print("\n   Step 3.3: import agenticraft.core.reasoning")
try:
    import agenticraft.core.reasoning
    print("   ✅ Success")
    print(f"      __file__ = {agenticraft.core.reasoning.__file__}")
    print(f"      __all__ = {agenticraft.core.reasoning.__all__}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

# Step 4: The problematic import
print("\n   Step 3.4: from agenticraft.core import reasoning")
try:
    from agenticraft.core import reasoning
    print("   ✅ Success!")
except ImportError as e:
    print(f"   ❌ Failed: {e}")
    
    # Let's check what Python is trying to do
    print("\n   Detailed error analysis:")
    error_msg = str(e)
    print(f"   Error message: '{error_msg}'")
    
    # Check exception attributes
    if hasattr(e, 'name'):
        print(f"   Missing name: {e.name}")
    if hasattr(e, 'path'):
        print(f"   Path: {e.path}")
    
    # Try to understand why
    print("\n   Checking if reasoning is accessible:")
    if 'agenticraft.core' in sys.modules:
        core_module = sys.modules['agenticraft.core']
        print(f"   agenticraft.core is loaded")
        
        # Check if reasoning is an attribute
        if hasattr(core_module, 'reasoning'):
            print("   ✅ core has 'reasoning' attribute")
        else:
            print("   ❌ core does NOT have 'reasoning' attribute")
            
            # Check what attributes it does have
            attrs = [a for a in dir(core_module) if not a.startswith('_')]
            print(f"   Available attributes: {attrs[:10]}...")

print("\n" + "=" * 60)
print("Diagnosis complete!")
