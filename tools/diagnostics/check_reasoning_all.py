#!/usr/bin/env python3
"""Check reasoning.py for __all__ definition."""

# Read the file and check for __all__
with open("/Users/zahere/Desktop/TLV/agenticraft/agenticraft/core/reasoning.py", "r") as f:
    content = f.read()
    
# Look for __all__ definition
if "__all__" in content:
    # Extract the __all__ definition
    lines = content.split('\n')
    in_all = False
    all_content = []
    
    for line in lines:
        if "__all__" in line and "=" in line:
            in_all = True
            all_content.append(line)
        elif in_all:
            all_content.append(line)
            if "]" in line:
                break
    
    print("Found __all__ definition:")
    print("\n".join(all_content))
else:
    print("No __all__ definition found in reasoning.py")

# Also check for any references to ThoughtProcess
if "ThoughtProcess" in content:
    print("\n⚠️  Found references to ThoughtProcess!")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "ThoughtProcess" in line:
            print(f"Line {i+1}: {line.strip()}")
else:
    print("\n✅ No references to ThoughtProcess in reasoning.py")
