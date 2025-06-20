#!/usr/bin/env python3
"""
Final verification that all import errors are resolved.
"""

import sys
import subprocess
import os

def test_all_imports():
    """Test all the imports that were having issues."""
    
    print("Testing All Import Fixes")
    print("=" * 60)
    
    # Change to project directory
    os.chdir("/Users/zahere/Desktop/TLV/agenticraft")
    
    test_imports = [
        # Core imports
        ("Core BaseTool", "from agenticraft.core import BaseTool"),
        ("Core WorkflowConfig", "from agenticraft.core import WorkflowConfig"),
        
        # Auth imports
        ("Auth JWTAuth", "from agenticraft.core.auth import JWTAuth"),
        ("Auth APIKeyAuth", "from agenticraft.core.auth import APIKeyAuth"),
        
        # Fabric imports (with protocol stubs)
        ("Fabric Unified", "from agenticraft.fabric.agent import UnifiedProtocolFabric"),
        
        # MCP imports
        ("MCP mcp_tool", "from agenticraft.protocols.mcp import mcp_tool"),
        ("MCP wrap_function", "from agenticraft.protocols.mcp import wrap_function_as_mcp_tool"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_stmt in test_imports:
        try:
            exec(import_stmt, {})
            print(f"✅ {name}")
            passed += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    
    # Now test pytest collection
    print("\nTesting pytest collection...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True
    )
    
    if "ImportError" in result.stderr:
        print("❌ Still have import errors in test collection:")
        # Extract first import error
        for line in result.stderr.split('\n'):
            if "ImportError:" in line:
                print(f"   {line}")
                break
    else:
        # Count collected items
        collected = result.stdout.count("::")
        print(f"✅ Test collection successful! Collected {collected} tests")
    
    print("\n" + "=" * 60)
    print(f"Import test results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All imports are now working!")
        print("\nYou can run tests with: pytest -xvs")
    else:
        print("\n⚠️  Some imports still need fixing")

if __name__ == '__main__':
    test_all_imports()
