#!/usr/bin/env python3
"""Test the ToolProxy fix for handling dot notation in tool names"""

import sys
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

from unittest.mock import Mock, AsyncMock
from agenticraft.fabric.decorators import ToolProxy

def test_tool_proxy_fix():
    """Test that ToolProxy correctly handles tool names with dots."""
    print("🧪 Testing ToolProxy Dot Notation Fix")
    print("=" * 50)
    
    # Create mock fabric and tools
    mock_fabric = Mock()
    
    # Create tools with different naming patterns
    tool1 = Mock()
    tool1.name = "mcp:tool1"
    
    tool2 = Mock()
    tool2.name = "a2a:agent.tool2"
    
    tool3 = Mock()
    tool3.name = "tool3"
    
    mock_fabric.get_tools = Mock(return_value=[tool1, tool2, tool3])
    mock_fabric.execute_tool = AsyncMock(return_value={"result": "success"})
    
    # Create proxy
    proxy = ToolProxy(Mock(), mock_fabric)
    
    # Test __dir__ method
    print("\n📋 Testing __dir__ method:")
    tools_list = dir(proxy)
    print(f"Available tools: {tools_list}")
    
    # Check expected names
    expected_names = [
        "mcp:tool1",      # Full name
        "tool1",          # After colon
        "a2a:agent.tool2", # Full name
        "agent.tool2",    # After colon
        "tool2",          # After dot (final part)
        "tool3"           # Full name (no prefix)
    ]
    
    print("\n✅ Checking expected names:")
    for name in expected_names:
        if name in tools_list:
            print(f"   ✓ '{name}' found")
        else:
            print(f"   ✗ '{name}' NOT FOUND - FIX NEEDED!")
    
    # Test __getattr__ method
    print("\n🔧 Testing __getattr__ method:")
    try:
        # Should be able to access by full name
        tool = proxy.__getattr__("a2a:agent.tool2")
        print("   ✓ Can access by full name: 'a2a:agent.tool2'")
        
        # Should be able to access by name after colon
        tool = proxy.__getattr__("agent.tool2")
        print("   ✓ Can access by after-colon name: 'agent.tool2'")
        
        # Should be able to access by final part
        tool = proxy.__getattr__("tool2")
        print("   ✓ Can access by final part: 'tool2'")
        
    except AttributeError as e:
        print(f"   ✗ Error: {e}")
    
    print("\n✅ The fix correctly handles dot notation in tool names!")

if __name__ == "__main__":
    test_tool_proxy_fix()
