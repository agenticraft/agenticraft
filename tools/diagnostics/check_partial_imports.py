#!/usr/bin/env python3
"""Check sys.modules after a failed import to see what's partially loaded."""

import sys

# Store initial modules
initial_modules = set(sys.modules.keys())

print("Checking sys.modules after failed import...")
print("=" * 60)

# Clear agenticraft modules
for k in list(sys.modules.keys()):
    if k.startswith('agenticraft'):
        del sys.modules[k]

print("\nBefore import:")
agenti_modules = [k for k in sys.modules.keys() if 'agenticraft' in k]
print(f"  AgentiCraft modules in sys.modules: {len(agenti_modules)}")

try:
    from agenticraft.core import reasoning
    print("✅ Import succeeded (unexpected!)")
except ImportError as e:
    print(f"❌ ImportError as expected: {e}")
    
    # Check what modules were partially loaded
    print("\nAfter failed import:")
    new_modules = set(sys.modules.keys()) - initial_modules
    agenti_new = [m for m in new_modules if 'agenticraft' in m]
    
    print(f"  New modules loaded: {len(new_modules)}")
    print(f"  New AgentiCraft modules: {len(agenti_new)}")
    
    for mod in sorted(agenti_new):
        print(f"    - {mod}")
        
        # Check if the module has issues
        module = sys.modules.get(mod)
        if module:
            # Check if it has __all__
            if hasattr(module, '__all__'):
                print(f"      __all__ = {module.__all__[:3]}..." if len(module.__all__) > 3 else f"      __all__ = {module.__all__}")
            
            # Check for ThoughtProcess
            if hasattr(module, 'ThoughtProcess'):
                print(f"      ⚠️  Has ThoughtProcess attribute!")

# Now let's check if reasoning module is partially loaded
print("\n" + "-" * 60)
print("Checking if reasoning module is in sys.modules:")

if 'agenticraft.core.reasoning' in sys.modules:
    print("✅ reasoning module IS in sys.modules")
    reasoning = sys.modules['agenticraft.core.reasoning']
    
    # Check its state
    print(f"  Module: {reasoning}")
    print(f"  File: {getattr(reasoning, '__file__', 'Unknown')}")
    
    # Check __all__
    if hasattr(reasoning, '__all__'):
        print(f"  __all__ defined: {reasoning.__all__}")
        
        # Check each item
        for item in reasoning.__all__:
            if hasattr(reasoning, item):
                print(f"    ✅ {item}")
            else:
                print(f"    ❌ {item} (missing!)")
else:
    print("❌ reasoning module NOT in sys.modules")
