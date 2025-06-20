#!/usr/bin/env python3
"""
Verify and validate the refactoring status.
This script checks:
1. The new structure is in place
2. Old files have been removed/moved
3. Tests are aligned with the new structure
4. No broken imports remain
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple

BASE_DIR = Path(__file__).parent


class RefactoringVerifier:
    def __init__(self):
        self.base_dir = BASE_DIR
        self.errors = []
        self.warnings = []
        self.success = []
        
    def verify_new_structure(self) -> bool:
        """Verify the new refactored structure is in place."""
        print("🔍 Verifying new structure...")
        
        # Core modules that should exist
        core_modules = [
            "core/transport/base.py",
            "core/transport/http.py",
            "core/transport/websocket.py",
            "core/auth/base.py",
            "core/auth/strategies.py",  # Changed from providers.py
            "core/registry/base.py",
            "core/patterns/client_server.py",  # Changed from base.py
            "core/serialization/base.py",  # Changed from serialization.py
            "core/exceptions.py"
        ]
        
        # Protocol modules
        protocol_modules = [
            "protocols/base.py",
            "protocols/mcp/protocol.py",
            "protocols/a2a/protocol.py"
        ]
        
        # Fabric modules
        fabric_modules = [
            "fabric/agent.py",
            "fabric/builder.py",
            "fabric/config.py",
            "fabric/protocol_types.py",
            "fabric/protocol_adapters.py",
            "fabric/extensions.py",
            "fabric/legacy.py"
        ]
        
        all_modules = core_modules + protocol_modules + fabric_modules
        missing = []
        
        for module_path in all_modules:
            full_path = self.base_dir / "agenticraft" / module_path
            if not full_path.exists():
                missing.append(module_path)
                self.errors.append(f"Missing required module: {module_path}")
        
        if not missing:
            self.success.append("✅ All required modules exist")
            return True
        else:
            return False
    
    def check_old_files_removed(self) -> bool:
        """Check that old redundant files have been removed."""
        print("\n🔍 Checking for redundant files...")
        
        old_files = [
            "fabric/unified.py",
            "fabric/unified_enhanced.py",
            "fabric/adapters_base.py",
            "utils/config.py",
            "security/auth.py"
        ]
        
        still_exists = []
        
        for file_path in old_files:
            full_path = self.base_dir / "agenticraft" / file_path
            if full_path.exists():
                still_exists.append(file_path)
                self.warnings.append(f"Old file still exists: {file_path}")
        
        if not still_exists:
            self.success.append("✅ All old files have been removed")
            return True
        else:
            return False
    
    def find_problematic_imports(self) -> Dict[str, List[str]]:
        """Find imports of removed/refactored modules."""
        print("\n🔍 Checking for problematic imports...")
        
        problematic_patterns = [
            (r"from\s+agenticraft\.fabric\.unified\s+import", "fabric.unified"),
            (r"from\s+agenticraft\.fabric\.unified_enhanced\s+import", "fabric.unified_enhanced"),
            (r"from\s+agenticraft\.fabric\.agent_enhanced\s+import", "fabric.agent_enhanced"),
            (r"from\s+agenticraft\.fabric\.sdk_fabric\s+import", "fabric.sdk_fabric"),
            (r"from\s+agenticraft\.utils\.config\s+import", "utils.config"),
            (r"from\s+agenticraft\.security\.auth\s+import", "security.auth"),
            (r"import\s+agenticraft\.fabric\.unified", "fabric.unified"),
            (r"import\s+agenticraft\.fabric\.unified_enhanced", "fabric.unified_enhanced")
        ]
        
        issues = {}
        
        for py_file in self.base_dir.rglob("*.py"):
            # Skip cache, build, and backup directories
            if any(part in str(py_file) for part in ['__pycache__', 'build', 'dist', '.git', 'venv', 'backup', 'refactoring_backup']):
                continue
                
            # Skip if it's a directory
            if py_file.is_dir():
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, module_name in problematic_patterns:
                    if re.search(pattern, content):
                        rel_path = str(py_file.relative_to(self.base_dir))
                        if rel_path not in issues:
                            issues[rel_path] = []
                        issues[rel_path].append(module_name)
            except Exception as e:
                self.warnings.append(f"Could not read {py_file}: {e}")
        
        if not issues:
            self.success.append("✅ No problematic imports found")
        else:
            for file_path, modules in issues.items():
                self.errors.append(f"File {file_path} imports: {', '.join(modules)}")
        
        return issues
    
    def verify_test_imports(self) -> bool:
        """Verify test files use correct imports."""
        print("\n🔍 Verifying test imports...")
        
        correct_imports = {
            "UnifiedAgent": "from agenticraft.fabric import UnifiedAgent",
            "AgentBuilder": "from agenticraft.fabric import AgentBuilder",
            "ProtocolType": "from agenticraft.fabric import ProtocolType",
            "MCPAdapter": "from agenticraft.fabric import MCPAdapter",
            "EnhancedUnifiedProtocolFabric": "from agenticraft.fabric import EnhancedUnifiedProtocolFabric"
        }
        
        test_dir = self.base_dir / "tests"
        issues_found = False
        
        for test_file in test_dir.rglob("test_*.py"):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse AST to find imports
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "agenticraft" in node.module:
                            # Check if it's importing from the right place
                            for alias in node.names:
                                name = alias.name
                                if name in correct_imports:
                                    expected = correct_imports[name]
                                    actual = f"from {node.module} import {name}"
                                    
                                    # Check if it's importing from the right place
                                    # Allow both direct imports and submodule imports for backwards compatibility
                                    if node.module not in expected:
                                        # Special case: Allow importing from .legacy for backwards compatibility items
                                        if name == "EnhancedUnifiedProtocolFabric" and "legacy" in node.module:
                                            continue  # This is acceptable
                                        # Only warn if it's really wrong
                                        if "fabric" not in node.module or name not in str(node.module):
                                            self.warnings.append(
                                                f"{test_file.name}: {name} imported from {node.module}, "
                                                f"expected in {expected}"
                                            )
                                            issues_found = True
            except Exception as e:
                self.warnings.append(f"Could not parse {test_file}: {e}")
        
        if not issues_found:
            self.success.append("✅ Test imports look correct")
        
        return not issues_found
    
    def check_backwards_compatibility(self) -> bool:
        """Check if backwards compatibility layer is in place."""
        print("\n🔍 Checking backwards compatibility...")
        
        compat_file = self.base_dir / "agenticraft/fabric/compat/__init__.py"
        
        if not compat_file.exists():
            self.errors.append("Compatibility layer missing: fabric/compat/__init__.py")
            return False
        
        try:
            with open(compat_file, 'r') as f:
                content = f.read()
                
            # Check for key compatibility imports
            required_compat = [
                "UnifiedFabric",
                "create_sdk_agent",
                "warnings.warn"
            ]
            
            missing = []
            for item in required_compat:
                if item not in content:
                    missing.append(item)
            
            if missing:
                self.warnings.append(f"Compatibility layer missing: {', '.join(missing)}")
                return False
            else:
                self.success.append("✅ Backwards compatibility layer is in place")
                return True
        except Exception as e:
            self.errors.append(f"Could not check compatibility layer: {e}")
            return False
    
    def run_verification(self) -> bool:
        """Run all verification checks."""
        print("=" * 80)
        print("AGENTICRAFT REFACTORING VERIFICATION")
        print("=" * 80)
        
        checks = [
            ("New Structure", self.verify_new_structure),
            ("Old Files Removed", self.check_old_files_removed),
            ("Problematic Imports", lambda: not bool(self.find_problematic_imports())),
            ("Test Imports", self.verify_test_imports),
            ("Backwards Compatibility", self.check_backwards_compatibility)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            passed = check_func()
            if not passed:
                all_passed = False
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if self.success:
            print("\n✅ SUCCESSES:")
            for msg in self.success:
                print(f"  {msg}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for msg in self.errors:
                print(f"  {msg}")
        
        print("\n" + "=" * 80)
        
        if all_passed and not self.errors:
            print("✅ REFACTORING VERIFICATION PASSED!")
            print("\nThe refactoring appears to be complete and consistent.")
        else:
            print("❌ REFACTORING VERIFICATION FAILED!")
            print("\nThere are issues that need to be addressed.")
        
        return all_passed


def main():
    """Run the verification."""
    verifier = RefactoringVerifier()
    success = verifier.run_verification()
    
    # Create a report file
    report_path = BASE_DIR / "refactoring_verification_report.md"
    
    with open(report_path, 'w') as f:
        f.write("# Refactoring Verification Report\n\n")
        f.write(f"Generated: {Path(__file__).name}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Total Errors: {len(verifier.errors)}\n")
        f.write(f"- Total Warnings: {len(verifier.warnings)}\n")
        f.write(f"- Total Successes: {len(verifier.success)}\n\n")
        
        if verifier.success:
            f.write("## ✅ Successes\n\n")
            for msg in verifier.success:
                f.write(f"- {msg}\n")
            f.write("\n")
        
        if verifier.warnings:
            f.write("## ⚠️ Warnings\n\n")
            for msg in verifier.warnings:
                f.write(f"- {msg}\n")
            f.write("\n")
        
        if verifier.errors:
            f.write("## ❌ Errors\n\n")
            for msg in verifier.errors:
                f.write(f"- {msg}\n")
            f.write("\n")
        
        f.write("## Recommendations\n\n")
        if verifier.errors:
            f.write("1. Fix the errors listed above\n")
            f.write("2. Run tests to ensure functionality\n")
            f.write("3. Update imports in affected files\n")
        elif verifier.warnings:
            f.write("1. Review the warnings and address if needed\n")
            f.write("2. Consider running the cleanup script\n")
            f.write("3. Update documentation if needed\n")
        else:
            f.write("1. The refactoring appears complete!\n")
            f.write("2. Consider running the cleanup script to remove redundant files\n")
            f.write("3. Update the main README with the refactored version\n")
    
    print(f"\n📄 Report saved to: {report_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
