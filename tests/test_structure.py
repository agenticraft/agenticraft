"""
Test to validate the project structure is set up correctly.
"""

import os
from pathlib import Path

import pytest


@pytest.mark.structure
def test_project_structure():
    """Validate the basic project structure exists."""
    root = Path(__file__).parent.parent
    
    # Core directories that must exist
    required_dirs = [
        "agenticraft/core",
        "agenticraft/protocols/mcp",
        "agenticraft/agents",
        "agenticraft/tools", 
        "agenticraft/memory",
        "agenticraft/providers",
        "agenticraft/plugins",
        "agenticraft/workflows",
        "agenticraft/telemetry",
        "agenticraft/cli",
        "agenticraft/templates",
        "examples",
        "tests",
        "docs",
    ]
    
    for dir_path in required_dirs:
        assert (root / dir_path).exists(), f"Missing directory: {dir_path}"


@pytest.mark.structure
def test_init_files():
    """Ensure all packages have __init__.py files."""
    root = Path(__file__).parent.parent / "agenticraft"
    
    for path in root.rglob("*/"):
        if path.is_dir() and not path.name.startswith("__"):
            init_file = path / "__init__.py"
            assert init_file.exists(), f"Missing __init__.py in {path}"


@pytest.mark.unit
def test_imports():
    """Test that basic imports work."""
    # First ensure we can import without errors
    import agenticraft
    from agenticraft.core import exceptions, config
    
    # Check version
    assert hasattr(agenticraft, '__version__')
    assert agenticraft.__version__ == "0.1.0"
    
    # Verify some basic imports work
    assert hasattr(exceptions, 'AgentError')
    assert hasattr(config, 'settings')
