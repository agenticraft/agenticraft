#!/usr/bin/env python3
"""Test the Mock configuration fix"""

import sys
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

from unittest.mock import Mock

def test_mock_fix():
    """Test that Mock objects are configured correctly."""
    print("🧪 Testing Mock Configuration Fix")
    print("=" * 50)
    
    # OLD WAY (incorrect)
    print("\n❌ OLD WAY (incorrect):")
    mock_old = Mock(name="mcp:search")
    print(f"mock_old.name type: {type(mock_old.name)}")
    print(f"mock_old.name value: {mock_old.name}")
    try:
        result = mock_old.name.split(":")
        print(f"Split result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # NEW WAY (correct)
    print("\n✅ NEW WAY (correct):")
    mock_new = Mock()
    mock_new.name = "mcp:search"
    print(f"mock_new.name type: {type(mock_new.name)}")
    print(f"mock_new.name value: {mock_new.name}")
    try:
        result = mock_new.name.split(":")
        print(f"Split result: {result}")
        print(f"Last part: {result[-1]}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✅ The fix correctly configures Mock attributes!")

if __name__ == "__main__":
    test_mock_fix()
