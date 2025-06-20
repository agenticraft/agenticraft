#!/usr/bin/env python3
"""Final diagnosis - check what's actually in __all__ and if it matches defined items."""

# Read and parse reasoning.py
with open('/Users/zahere/Desktop/TLV/agenticraft/agenticraft/core/reasoning.py', 'r') as f:
    lines = f.readlines()

print("Analyzing reasoning.py file...")
print("=" * 60)

# Find __all__ definition
all_items = []
in_all = False
for i, line in enumerate(lines):
    if '__all__' in line and '=' in line:
        in_all = True
        print(f"\nFound __all__ at line {i+1}:")
    
    if in_all:
        print(f"  Line {i+1}: {line.rstrip()}")
        
        # Extract items from the line
        if '"' in line:
            import re
            matches = re.findall(r'"([^"]+)"', line)
            all_items.extend(matches)
        
        if ']' in line:
            in_all = False
            break

print(f"\n__all__ contains these {len(all_items)} items:")
for item in all_items:
    print(f"  - {item}")

# Check if ThoughtProcess is in there
if 'ThoughtProcess' in all_items:
    print("\n⚠️  ERROR: ThoughtProcess IS in __all__!")
    print("This is the problem - it's listed in __all__ but not defined in the module.")
else:
    print("\n✅ ThoughtProcess is NOT in __all__")

# Now find all class definitions
print("\nClass definitions in the file:")
class_names = []
for i, line in enumerate(lines):
    if line.strip().startswith('class ') and '(' in line:
        class_name = line.strip().split()[1].split('(')[0].rstrip(':')
        class_names.append(class_name)
        print(f"  Line {i+1}: class {class_name}")

print(f"\nTotal classes defined: {len(class_names)}")

# Check for mismatches
print("\nChecking for mismatches:")
for item in all_items:
    if item not in class_names:
        print(f"  ❌ '{item}' is in __all__ but not defined as a class!")

print("\nDiagnosis complete!")
