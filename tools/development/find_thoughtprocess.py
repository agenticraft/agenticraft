#!/usr/bin/env python3
"""Find all references to ThoughtProcess in the codebase."""

import os
import sys

def find_in_file(filepath, search_term):
    """Search for a term in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_term in content:
                # Find the lines containing the term
                lines = content.split('\n')
                matches = []
                for i, line in enumerate(lines):
                    if search_term in line:
                        matches.append((i + 1, line.strip()))
                return matches
    except Exception:
        pass
    return []

def search_directory(root_dir, search_term, exclude_dirs=None):
    """Search for a term in all Python files in a directory."""
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', 'venv', 'site', 'dist', '.pytest_cache'}
    
    results = {}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                matches = find_in_file(filepath, search_term)
                if matches:
                    results[filepath] = matches
    
    return results

# Search for ThoughtProcess
print("Searching for 'ThoughtProcess' in AgentiCraft codebase...")
print("=" * 60)

agenticraft_dir = "/Users/zahere/Desktop/TLV/agenticraft"
results = search_directory(agenticraft_dir, "ThoughtProcess")

if results:
    for filepath, matches in results.items():
        rel_path = os.path.relpath(filepath, agenticraft_dir)
        print(f"\n📄 {rel_path}")
        for line_num, line in matches:
            print(f"   Line {line_num}: {line}")
else:
    print("\n✅ No references to 'ThoughtProcess' found in the codebase!")

# Also search for partial matches
print("\n" + "=" * 60)
print("Searching for 'Thought' (partial matches)...")
print("=" * 60)

thought_results = search_directory(agenticraft_dir, "Thought")
if thought_results:
    # Filter to show only imports and class definitions
    for filepath, matches in thought_results.items():
        rel_path = os.path.relpath(filepath, agenticraft_dir)
        filtered_matches = [(num, line) for num, line in matches 
                          if 'import' in line or 'class' in line or '__all__' in line]
        if filtered_matches:
            print(f"\n📄 {rel_path}")
            for line_num, line in filtered_matches[:5]:  # Show max 5 matches per file
                print(f"   Line {line_num}: {line}")
