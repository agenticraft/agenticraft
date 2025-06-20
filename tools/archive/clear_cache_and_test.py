#!/usr/bin/env python3
"""Clear Python cache files and test import again."""

import os
import shutil
import sys

print("Clearing Python cache files...")
print("=" * 60)

# Find all __pycache__ directories in agenticraft
agenticraft_root = "/Users/zahere/Desktop/TLV/agenticraft/agenticraft"
pycache_dirs = []

for root, dirs, files in os.walk(agenticraft_root):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        pycache_dirs.append(pycache_path)

print(f"\nFound {len(pycache_dirs)} __pycache__ directories:")
for dir in pycache_dirs:
    rel_path = os.path.relpath(dir, agenticraft_root)
    print(f"  - {rel_path}")

# Clear them
if input("\nDelete these cache directories? (y/n): ").lower() == 'y':
    for dir in pycache_dirs:
        try:
            shutil.rmtree(dir)
            print(f"  ✅ Deleted: {os.path.relpath(dir, agenticraft_root)}")
        except Exception as e:
            print(f"  ❌ Failed to delete {dir}: {e}")
    
    print("\n✅ Cache cleared!")
else:
    print("\n⚠️  Cache not cleared.")

# Also clear sys.modules
print("\nClearing sys.modules...")
modules_to_clear = [k for k in sys.modules.keys() if k.startswith('agenticraft')]
for mod in modules_to_clear:
    del sys.modules[mod]
print(f"Cleared {len(modules_to_clear)} modules from sys.modules")

# Now test the import
print("\n" + "-" * 60)
print("Testing import after cache clear:")

try:
    from agenticraft.core import reasoning
    print("✅ Import successful!")
    print(f"   reasoning.__all__ = {reasoning.__all__}")
except ImportError as e:
    print(f"❌ Import still fails: {e}")
    
    # One more diagnostic
    print("\nTrying alternative import:")
    try:
        import agenticraft.core.reasoning
        print("✅ Direct import works")
        
        # Can we access it through core?
        import agenticraft.core
        reasoning = getattr(agenticraft.core, 'reasoning', None)
        if reasoning:
            print("✅ Can access through getattr")
        else:
            print("❌ Cannot access through getattr")
            
    except Exception as e2:
        print(f"❌ Direct import also fails: {e2}")

print("\nDone!")
