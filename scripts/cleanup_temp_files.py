#!/usr/bin/env python3
"""Clean up temporary test files."""
import os
import shutil

# Files to remove (temporary test scripts)
files_to_remove = [
    "run_test.py",
    "verify_config_tests.py", 
    "verify_plugin_tests.py",
    "verify_tests.py",
    "test_after_exception_fix.py",
    "test_after_fix.py",
    "test_client_fix.py",
    "test_collection.py",
    "test_comprehensive_files.py",
    "test_day4.py",
    "test_day4_basic.py",
    "test_day4_core.py",
    "test_day5_cli.py",
    "test_day5_final.py",
    "test_day5_quick.py",
    "test_imports.py",
    "test_imports_agent.py",
    "test_imports_detailed.py",
    "test_individual_modules.py",
    "test_json_tools.py",
    "test_mcp_agent_integration.py",
    "test_mcp_fix.py",
    "test_mcp_integration.py",
    "test_minimal.py",
    "test_mock_behavior.py",
    "test_mock_fix.py",
    "test_plugin_final.py",
    "test_plugin_fix.py",
    "test_plugins_only.py",
    "test_quick.py",
    "test_simple.py",
    "test_system.py",
    "test_tool_error_fix.py",
    "debug_plugin_test.py",
    "debug_tests.py",
    "example_test_exceptions.py",
    "find_test_tool_warnings.py",
    "find_test_tools.py",
    "run_agent_tests.py",
    "run_basic_tests.py",
    "run_day6_tests.py",
    "run_integration_tests.py",
    "run_mcp_tests.py",
    "run_structure_tests.py",
    "run_tool_tests.py",
    "run_unit_tests.py",
    "verify_mcp_fixes.py",
]

# Clean up
removed_count = 0
for filename in files_to_remove:
    filepath = f"/Users/zahere/Desktop/TLV/agenticraft/{filename}"
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"✓ Removed {filename}")
        removed_count += 1

print(f"\n✅ Cleaned up {removed_count} temporary test files")
