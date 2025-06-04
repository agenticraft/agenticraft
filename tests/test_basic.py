#!/usr/bin/env python3
"""Simple unit test to verify basic functionality."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_basic_import():
    """Test that we can import core modules."""
    try:
        import agenticraft
        print("✅ Can import agenticraft")
    except ImportError as e:
        print(f"❌ Cannot import agenticraft: {e}")
        return False
    
    try:
        from agenticraft.core.agent import Agent
        print("✅ Can import Agent")
    except ImportError as e:
        print(f"❌ Cannot import Agent: {e}")
        return False
    
    try:
        from agenticraft.core.tool import Tool
        print("✅ Can import Tool")
    except ImportError as e:
        print(f"❌ Cannot import Tool: {e}")
        return False
    
    return True

def test_basic_agent_creation():
    """Test basic agent creation."""
    try:
        from agenticraft.core.agent import Agent
        
        # Create a simple agent
        agent = Agent(
            name="Test Agent",
            role="Testing"
        )
        
        assert agent.name == "Test Agent"
        assert agent.role == "Testing"
        print("✅ Can create basic agent")
        return True
    except Exception as e:
        print(f"❌ Cannot create agent: {e}")
        return False

def main():
    """Run basic tests."""
    print("🧪 Running Basic AgentiCraft Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_basic_import():
        all_passed = False
    
    # Test agent creation
    if not test_basic_agent_creation():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All basic tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
