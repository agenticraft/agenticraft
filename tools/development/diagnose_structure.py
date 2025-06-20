#!/usr/bin/env python3
"""
Quick diagnostic to understand the actual AgentiCraft structure.
This will help identify the correct import paths.
"""

import os
import sys
from pathlib import Path

def explore_module(module_path, indent=0):
    """Recursively explore a module directory."""
    items = []
    
    if not module_path.exists():
        return [f"{'  ' * indent}❌ Path does not exist: {module_path}"]
    
    try:
        for item in sorted(module_path.iterdir()):
            if item.name.startswith('.') or item.name == '__pycache__':
                continue
                
            if item.is_file() and item.suffix == '.py':
                items.append(f"{'  ' * indent}📄 {item.name}")
                
                # Try to read imports from the file
                if indent < 2:  # Only check first two levels
                    try:
                        with open(item, 'r') as f:
                            lines = f.readlines()[:20]  # First 20 lines
                            for line in lines:
                                if line.strip().startswith('class ') and not line.strip().startswith('class _'):
                                    class_name = line.strip().split('(')[0].replace('class ', '')
                                    items.append(f"{'  ' * (indent+1)}  └─ class {class_name}")
                    except:
                        pass
                        
            elif item.is_dir():
                items.append(f"{'  ' * indent}📁 {item.name}/")
                items.extend(explore_module(item, indent + 1))
                
    except PermissionError:
        items.append(f"{'  ' * indent}❌ Permission denied")
        
    return items

def main():
    """Explore AgentiCraft structure."""
    print("🔍 AgentiCraft Module Structure Explorer\n")
    
    base_path = Path(__file__).parent
    agenticraft_path = base_path / "agenticraft"
    
    if not agenticraft_path.exists():
        print(f"❌ AgentiCraft module not found at: {agenticraft_path}")
        return
    
    # Key modules to explore
    modules = [
        "security",
        "protocols",
        "production"
    ]
    
    for module in modules:
        module_path = agenticraft_path / module
        print(f"\n{'='*60}")
        print(f"📦 {module.upper()} MODULE")
        print(f"{'='*60}")
        
        items = explore_module(module_path)
        for item in items:
            print(item)
    
    # Check specific imports
    print(f"\n{'='*60}")
    print("🔍 IMPORT PATH CHECKS")
    print(f"{'='*60}\n")
    
    # Add agenticraft to path
    sys.path.insert(0, str(base_path))
    
    imports_to_check = [
        ("Security Manager", "from agenticraft.security import get_security_manager"),
        ("Sandbox Manager", "from agenticraft.security.sandbox import get_sandbox_manager"),
        ("Sandbox Types", "from agenticraft.security.abstractions.types import SandboxType"),
        ("Security Context", "from agenticraft.security.abstractions.interfaces import SecurityContext"),
        ("A2A Registry", "from agenticraft.protocols.a2a.registry import ProtocolRegistry"),
        ("MCP Client", "from agenticraft.protocols.mcp.client import MCPClient"),
    ]
    
    for name, import_stmt in imports_to_check:
        print(f"Testing: {name}")
        print(f"  Import: {import_stmt}")
        try:
            exec(import_stmt)
            print(f"  ✅ Success!")
        except ImportError as e:
            print(f"  ❌ ImportError: {e}")
        except Exception as e:
            print(f"  ⚠️  Other Error: {type(e).__name__}: {e}")
        print()

if __name__ == "__main__":
    main()
