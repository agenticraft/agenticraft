#!/usr/bin/env python3
"""
Refactoring file mover - helps organize AgentiCraft root directory files
"""

import os
import shutil
from pathlib import Path

# Define the base path
BASE_PATH = Path("/Users/zahere/Desktop/TLV/agenticraft")

# Define file movements
FILE_MOVEMENTS = {
    # Run files to scripts/
    "tools/scripts": [
        "run_all_security_tests_detailed.py",
        "run_all_toolproxy_tests.sh",
        "run_final_sdk_test.sh",
        "run_final_security_tests.py",
        "run_pytest_check.py",
        "run_sandbox_test.sh",
        "run_sdk_preference_test.sh",
        "run_sdk_test.sh",
        "run_sdk_tests.py",
        "run_security_tests_full.py",
        "run_single_test.sh",
        "run_specific_test.sh",
        "run_tests.sh",
        "run_tool_dir_test.sh",
        "run_visual_builder.py",
        "run_websocket_tests.sh",
    ],
    
    # Cleanup files to archive/
    "tools/archive": [
        "cleanup_check.py",
        "cleanup_redundant.py",
        "cleanup_redundant_files.py",
        "clean_cache.sh",
        "clear_and_diagnose.py",
        "fix_dependencies.sh",
        "clear_cache_and_test.py",
    ],
    
    # Test files to tests/
    "tests": [
        "test_a2a_fix.py",
        "test_a2a_hybrid_fix.py",
        "test_all_sdk_fixes.py",
        "test_auth.py.bak",
        "test_final_adapter_fixes.py",
        "test_mock_fix.py",
        "test_name_parsing.py",
        "test_refactoring_complete.py",
        "test_sandbox_basic.py",
        "test_sdk_integration_fix.py",
        "test_security_full.py",
        "test_security_imports.py",
        "test_security_quick.py",
        "test_timeout.py",
        "test_tool_proxy_fix.py",
        "test_websocket_fix.py",
    ],
    
    # Verify files to diagnostics/
    "tools/diagnostics": [
        "verify_all_fixes.py",
        "verify_all_imports.py",
        "verify_cleanup_safety.py",
        "verify_import_fix.py",
        "verify_refactoring_status.py",
        "verify_security_fix.py",
    ],
    
    # Other development files
    "tools/development": [
        "analyze_dependencies.py",
        "debug_import_error.py",
        "debug_reasoning_imports.py",
        "diagnose_structure.py",
        "final_diagnosis.py",
        "final_security_test_run.py",
        "final_verification.py",
        "find_import_error.py",
        "find_thoughtprocess.py",
        "minimal_error_test.py",
        "minimal_import_test.py",
        "prove_refactoring_complete.py",
        "quick_status.py",
        "refactor_tests.py",
        "validate_refactoring.py",
    ],
}

def move_files():
    """Move files to their appropriate directories."""
    moved_count = 0
    errors = []
    
    for target_dir, files in FILE_MOVEMENTS.items():
        target_path = BASE_PATH / target_dir
        
        # Ensure target directory exists
        target_path.mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            source = BASE_PATH / filename
            destination = target_path / filename
            
            if source.exists():
                try:
                    shutil.move(str(source), str(destination))
                    print(f"✓ Moved {filename} to {target_dir}/")
                    moved_count += 1
                except Exception as e:
                    error_msg = f"✗ Error moving {filename}: {e}"
                    print(error_msg)
                    errors.append(error_msg)
            else:
                # Check if already moved
                if destination.exists():
                    print(f"  {filename} already in {target_dir}/")
                else:
                    print(f"? {filename} not found")
    
    print(f"\n📊 Summary:")
    print(f"  Files moved: {moved_count}")
    print(f"  Errors: {len(errors)}")
    
    if errors:
        print("\n❌ Errors encountered:")
        for error in errors:
            print(f"  {error}")
    
    return moved_count, errors

if __name__ == "__main__":
    print("🚀 Starting AgentiCraft root directory cleanup...")
    print(f"   Base path: {BASE_PATH}\n")
    
    moved_count, errors = move_files()
    
    print("\n✅ Cleanup complete!")
