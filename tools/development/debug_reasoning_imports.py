#!/usr/bin/env python3
"""Debug script to find the exact import error."""

import sys
import traceback

print("Debugging AgentiCraft reasoning module imports...")

# Test 1: Try to import chain_of_thought directly
print("\n1. Testing direct import of chain_of_thought module:")
try:
    import agenticraft.reasoning.patterns.chain_of_thought as cot_module
    print("✓ Module imported successfully")
    print(f"   Module file: {cot_module.__file__}")
except ImportError as e:
    print(f"✗ Failed to import module: {e}")
    traceback.print_exc()

# Test 2: Try to import ChainOfThoughtReasoning from the module
print("\n2. Testing import of ChainOfThoughtReasoning class:")
try:
    from agenticraft.reasoning.patterns.chain_of_thought import ChainOfThoughtReasoning
    print("✓ ChainOfThoughtReasoning imported successfully")
except ImportError as e:
    print(f"✗ Failed to import ChainOfThoughtReasoning: {e}")
    traceback.print_exc()

# Test 3: Try importing through patterns
print("\n3. Testing import through patterns package:")
try:
    from agenticraft.reasoning.patterns import ChainOfThoughtReasoning
    print("✓ Import through patterns succeeded")
except ImportError as e:
    print(f"✗ Failed to import through patterns: {e}")
    traceback.print_exc()

# Test 4: Try importing from main reasoning module
print("\n4. Testing import from main reasoning module:")
try:
    from agenticraft.reasoning import ChainOfThoughtReasoning
    print("✓ Import from main module succeeded")
except ImportError as e:
    print(f"✗ Failed to import from main module: {e}")
    traceback.print_exc()

# Test 5: Check what happens with star import
print("\n5. Testing star import from patterns:")
try:
    from agenticraft.reasoning.patterns import *
    print("✓ Star import succeeded")
    if 'ChainOfThoughtReasoning' in locals():
        print("   ChainOfThoughtReasoning is in namespace")
except ImportError as e:
    print(f"✗ Star import failed: {e}")
    traceback.print_exc()

print("\nDebug complete!")
