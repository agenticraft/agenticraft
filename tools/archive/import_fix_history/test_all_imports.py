#!/usr/bin/env python3
"""
Quick test of all import fixes.
"""

import sys
import os

# Add project to path
sys.path.insert(0, '/Users/zahere/Desktop/TLV/agenticraft')

def test_imports():
    """Test all the imports that were fixed."""
    
    print("Testing AgentiCraft Import Fixes")
    print("=" * 50)
    
    imports_to_test = [
        # Core imports
        ("Core Agent", "from agenticraft.core import Agent"),
        ("Core BaseTool", "from agenticraft.core import BaseTool"),
        ("Core Tool", "from agenticraft.core import Tool"),
        ("Core Workflow", "from agenticraft.core import Workflow"),
        ("Core WorkflowConfig", "from agenticraft.core import WorkflowConfig"),
        
        # Auth imports
        ("Auth JWTAuth", "from agenticraft.core.auth import JWTAuth"),
        ("Auth APIKeyAuth", "from agenticraft.core.auth import APIKeyAuth"),
        ("Auth Providers", "from agenticraft.core.auth import JWTAuthProvider, APIKeyAuthProvider"),
        
        # Fabric imports
        ("Fabric UnifiedAgent", "from agenticraft.fabric import UnifiedAgent"),
        ("Fabric Unified Protocol", "from agenticraft.fabric.agent import UnifiedProtocolFabric"),
        ("Fabric MCPAdapter", "from agenticraft.fabric.agent import MCPAdapter"),
        ("Fabric ProtocolType", "from agenticraft.fabric.agent import ProtocolType"),
        
        # Workflow imports
        ("Research Team", "from agenticraft.workflows.research_team import ResearchTeam"),
        ("Code Review", "from agenticraft.workflows.code_review import CodeReviewPipeline"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_stmt in imports_to_test:
        try:
            exec(import_stmt, {})
            print(f"✅ {name:<25} - OK")
            passed += 1
        except ImportError as e:
            print(f"❌ {name:<25} - {str(e)[:50]}...")
            failed += 1
        except Exception as e:
            print(f"⚠️  {name:<25} - {type(e).__name__}: {str(e)[:40]}...")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All imports working correctly!")
        print("\nYou can now run tests with:")
        print("  cd /Users/zahere/Desktop/TLV/agenticraft")
        print("  pytest -xvs")
    else:
        print("\n⚠️  Some imports still failing")
        print("Check the errors above for details")

if __name__ == '__main__':
    test_imports()
