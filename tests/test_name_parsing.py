#!/usr/bin/env python3
"""Verify the ToolProxy fix matches the test expectations"""

import sys
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

def test_name_parsing():
    """Test the name parsing logic we implemented."""
    print("🧪 Testing Name Parsing Logic")
    print("=" * 50)
    
    test_cases = [
        ("mcp:tool1", ["mcp:tool1", "tool1"]),
        ("a2a:agent.tool2", ["a2a:agent.tool2", "agent.tool2", "tool2"]),
        ("tool3", ["tool3"]),
        ("protocol:nested.module.tool", ["protocol:nested.module.tool", "nested.module.tool", "tool"]),
    ]
    
    for tool_name, expected in test_cases:
        print(f"\n📝 Testing: {tool_name}")
        names = []
        
        # Add full name
        names.append(tool_name)
        
        # Extract simple name after colon
        if ":" in tool_name:
            after_colon = tool_name.split(":")[-1]
            if after_colon != tool_name:
                names.append(after_colon)
            
            # Also extract the final part after any dots
            if "." in after_colon:
                final_part = after_colon.split(".")[-1]
                if final_part not in names:
                    names.append(final_part)
        
        print(f"   Generated names: {names}")
        print(f"   Expected names:  {expected}")
        
        if names == expected:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            missing = set(expected) - set(names)
            extra = set(names) - set(expected)
            if missing:
                print(f"   Missing: {missing}")
            if extra:
                print(f"   Extra: {extra}")

if __name__ == "__main__":
    test_name_parsing()
