"""Generate the code reference pages automatically."""
from pathlib import Path

import mkdocs_gen_files

# Define the source code directory
src_root = Path("agenticraft")

# Generate pages for each Python module
for path in sorted(src_root.rglob("*.py")):
    # Skip __pycache__ and test files
    if "__pycache__" in str(path) or "test_" in path.name:
        continue
    
    # Skip __init__.py files that are empty or nearly empty
    if path.name == "__init__.py":
        if path.stat().st_size < 100:  # Skip small init files
            continue
    
    # Calculate the module path
    module_path = path.relative_to(src_root.parent).with_suffix("")
    doc_path = path.relative_to(src_root).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)
    
    # Calculate the Python module name
    parts = list(module_path.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
        if not parts:  # Skip root __init__.py
            continue
    
    # Generate the markdown content
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(parts)
        print(f"::: {identifier}", file=fd)
    
    # Update the nav
    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# Create the reference index page
with mkdocs_gen_files.open("reference/index.md", "w") as fd:
    fd.write("""# API Reference

This section contains the complete API reference for AgentiCraft.

## Core Components

- [`agenticraft.core.agent`](agent.md) - Base Agent class and functionality
- [`agenticraft.core.tool`](tool.md) - Tool decorators and abstractions
- [`agenticraft.core.workflow`](workflow.md) - Workflow engine
- [`agenticraft.core.memory`](memory.md) - Memory interfaces
- [`agenticraft.core.reasoning`](reasoning.md) - Reasoning patterns
- [`agenticraft.core.provider`](provider.md) - LLM provider interface

## Subsystems

- [`agenticraft.tools`](tools/index.md) - Built-in tools
- [`agenticraft.memory`](memory/index.md) - Memory implementations
- [`agenticraft.providers`](providers/index.md) - LLM provider integrations
- [`agenticraft.protocols.mcp`](protocols/mcp/index.md) - Model Context Protocol
- [`agenticraft.telemetry`](telemetry/index.md) - Observability components
- [`agenticraft.plugins`](plugins/index.md) - Plugin system

## CLI

- [`agenticraft.cli`](cli/index.md) - Command-line interface
""")

# Create a navigation file
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.write("""- [Overview](index.md)
- Core
  - [Agent](core/agent.md)
  - [Tool](core/tool.md)
  - [Workflow](core/workflow.md)
  - [Memory](core/memory.md)
  - [Reasoning](core/reasoning.md)
  - [Provider](core/provider.md)
  - [Exceptions](core/exceptions.md)
- Components
  - [Tools](tools/index.md)
  - [Memory](memory/index.md)
  - [Providers](providers/index.md)
  - [MCP](protocols/mcp/index.md)
  - [Telemetry](telemetry/index.md)
  - [Plugins](plugins/index.md)
  - [CLI](cli/index.md)
""")
