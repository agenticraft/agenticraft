#!/usr/bin/env python3
"""
Comprehensive import audit for AgentiCraft.
Identifies circular dependencies, missing imports, and other issues.
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, Set, List, Tuple

class ImportAnalyzer(ast.NodeVisitor):
    """Analyze imports in a Python file."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.imports = []
        self.from_imports = []
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module:
            module = node.module
            if node.level > 0:
                # Handle relative imports
                parts = str(self.file_path).split('/')
                if 'agenticraft' in parts:
                    idx = parts.index('agenticraft')
                    base_parts = parts[idx:-(1 + node.level)]
                    if base_parts:
                        module = '.'.join(base_parts) + '.' + module if module else '.'.join(base_parts)
            
            for alias in node.names:
                self.from_imports.append((module, alias.name))
        self.generic_visit(node)

def analyze_file(file_path: Path) -> Dict:
    """Analyze imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        analyzer = ImportAnalyzer(file_path)
        analyzer.visit(tree)
        
        return {
            'imports': analyzer.imports,
            'from_imports': analyzer.from_imports,
            'errors': []
        }
    except SyntaxError as e:
        return {
            'imports': [],
            'from_imports': [],
            'errors': [f'Syntax error: {e}']
        }
    except Exception as e:
        return {
            'imports': [],
            'from_imports': [],
            'errors': [f'Error: {e}']
        }

def get_module_path(import_name: str, base_path: Path) -> Path:
    """Convert import name to file path."""
    parts = import_name.split('.')
    path = base_path / '/'.join(parts)
    
    # Check for __init__.py (package)
    init_path = path / '__init__.py'
    if init_path.exists():
        return init_path
        
    # Check for .py file (module)
    py_path = Path(str(path) + '.py')
    if py_path.exists():
        return py_path
        
    return None

def build_dependency_graph(base_path: Path) -> Dict[str, Set[str]]:
    """Build a dependency graph of all modules."""
    graph = defaultdict(set)
    errors = defaultdict(list)
    
    # Directories to skip
    SKIP_DIRS = {
        'venv', '.venv', 'env', '.env',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        '.git', '.github', 'node_modules',
        'build', 'dist', 'egg-info', '.egg-info',
        'htmlcov', '.coverage', 'site',
        'docs/_build', 'exported_code',
        '.cleanup_temp', 'backup', 'backups'
    }
    
    # Find all Python files
    for py_file in base_path.rglob("*.py"):
        # Skip excluded directories
        if any(skip_dir in py_file.parts for skip_dir in SKIP_DIRS):
            continue
            
        # Skip non-agenticraft files
        if 'agenticraft' not in str(py_file):
            continue
            
        # Skip test files for now
        if 'test' in str(py_file) or 'tests' in str(py_file):
            continue
            
        # Get module name from path
        rel_path = py_file.relative_to(base_path)
        module_name = str(rel_path).replace('/', '.').replace('\\', '.')[:-3]
        if module_name.endswith('.__init__'):
            module_name = module_name[:-9]
            
        # Analyze imports
        analysis = analyze_file(py_file)
        
        if analysis['errors']:
            errors[module_name].extend(analysis['errors'])
            
        # Process imports
        for imp in analysis['imports']:
            if imp.startswith('agenticraft'):
                graph[module_name].add(imp)
                
        # Process from imports
        for module, name in analysis['from_imports']:
            if module and module.startswith('agenticraft'):
                graph[module_name].add(module)
                
    return graph, errors

def find_circular_dependencies(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Find circular dependencies in the graph."""
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: str, path: List[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                if len(cycle) > 2:  # Ignore self-imports
                    cycles.append(cycle)
                    
        rec_stack.remove(node)
        
    for node in graph:
        if node not in visited:
            dfs(node, [])
            
    # Remove duplicate cycles
    unique_cycles = []
    for cycle in cycles:
        normalized = tuple(sorted(cycle))
        if normalized not in [tuple(sorted(c)) for c in unique_cycles]:
            unique_cycles.append(cycle)
            
    return unique_cycles

def main():
    base_path = Path.cwd()
    
    if not (base_path / 'agenticraft').exists():
        print("Error: Run this from the AgentiCraft root directory")
        return 1
        
    print("🔍 AgentiCraft Import System Audit")
    print("=" * 50)
    print()
    
    # Build dependency graph
    print("Building dependency graph...")
    graph, errors = build_dependency_graph(base_path)
    
    # Report errors
    if errors:
        print(f"\n❌ Found {len(errors)} files with errors:")
        for module, errs in errors.items():
            print(f"\n  {module}:")
            for err in errs:
                print(f"    - {err}")
                
    # Find circular dependencies
    print("\n\nChecking for circular dependencies...")
    cycles = find_circular_dependencies(graph)
    
    if cycles:
        print(f"\n⚠️  Found {len(cycles)} circular dependencies:")
        for i, cycle in enumerate(cycles, 1):
            print(f"\n  Cycle {i}:")
            for j in range(len(cycle) - 1):
                print(f"    {cycle[j]} → {cycle[j+1]}")
    else:
        print("✅ No circular dependencies found!")
        
    # Analyze import depth
    print("\n\nAnalyzing import hierarchy...")
    
    # Group modules by depth
    depth_map = defaultdict(list)
    
    for module in graph:
        parts = module.split('.')
        if module.startswith('agenticraft'):
            depth = len(parts) - 1
            depth_map[depth].append(module)
            
    # Show hierarchy
    print("\nModule Hierarchy:")
    for depth in sorted(depth_map.keys()):
        print(f"\n  Level {depth}: ({len(depth_map[depth])} modules)")
        for module in sorted(depth_map[depth])[:5]:
            print(f"    - {module}")
        if len(depth_map[depth]) > 5:
            print(f"    ... and {len(depth_map[depth]) - 5} more")
            
    # Find modules with most dependencies
    print("\n\nModules with most dependencies:")
    dep_counts = [(m, len(deps)) for m, deps in graph.items()]
    dep_counts.sort(key=lambda x: x[1], reverse=True)
    
    for module, count in dep_counts[:10]:
        print(f"  {module}: {count} dependencies")
        
    # Find most imported modules
    print("\n\nMost frequently imported modules:")
    import_counts = defaultdict(int)
    for deps in graph.values():
        for dep in deps:
            import_counts[dep] += 1
            
    common_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)
    for module, count in common_imports[:10]:
        print(f"  {module}: imported {count} times")
        
    print("\n" + "=" * 50)
    print("Audit complete!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
