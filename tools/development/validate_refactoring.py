#!/usr/bin/env python3
"""
Refactoring validation script
Checks for common issues before and after refactoring
"""

import os
import ast
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple
import importlib.util
import subprocess

class RefactoringValidator:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.issues = []
        self.warnings = []
        
    def check_module_exists(self, module_path: str) -> bool:
        """Check if a module exists"""
        full_path = self.root_path / module_path
        return full_path.exists() or full_path.with_suffix('.py').exists()
        
    def check_required_modules(self):
        """Verify all required new modules exist"""
        print("Checking required modules...")
        
        required = [
            'agenticraft/core/transport',
            'agenticraft/core/auth', 
            'agenticraft/core/config',
            'agenticraft/fabric/agent'
        ]
        
        missing = []
        for module in required:
            if not self.check_module_exists(module):
                missing.append(module)
                self.issues.append(f"Required module missing: {module}")
                
        if not missing:
            print("✓ All required modules exist")
        else:
            print(f"✗ Missing {len(missing)} required modules")
            
    def find_circular_imports(self):
        """Detect potential circular imports"""
        print("\nChecking for circular imports...")
        
        # This is a simplified check - looks for files that import each other
        imports_map = {}
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    module_name = str(filepath.relative_to(self.root_path)).replace('/', '.').replace('.py', '')
                    
                    try:
                        with open(filepath, 'r') as f:
                            tree = ast.parse(f.read())
                            
                        imports = set()
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    if alias.name.startswith('agenticraft'):
                                        imports.add(alias.name)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module and node.module.startswith('agenticraft'):
                                    imports.add(node.module)
                                    
                        imports_map[module_name] = imports
                        
                    except:
                        pass
                        
        # Simple circular import detection
        for module1, imports1 in imports_map.items():
            for module2 in imports1:
                if module2 in imports_map and module1 in imports_map[module2]:
                    self.warnings.append(f"Potential circular import: {module1} <-> {module2}")
                    
        if not self.warnings:
            print("✓ No obvious circular imports detected")
        else:
            print(f"⚠️  Found {len(self.warnings)} potential circular imports")
            
    def validate_imports(self):
        """Validate all imports can be resolved"""
        print("\nValidating imports...")
        
        failed_files = []
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    
                    # Try to compile the file
                    try:
                        with open(filepath, 'rb') as f:
                            compile(f.read(), str(filepath), 'exec')
                    except SyntaxError as e:
                        failed_files.append((filepath, f"Syntax error: {e}"))
                    except Exception as e:
                        # This might be an import error
                        if 'import' in str(e).lower():
                            failed_files.append((filepath, str(e)))
                            
        if not failed_files:
            print("✓ All Python files compile successfully")
        else:
            print(f"✗ {len(failed_files)} files have compilation issues")
            for filepath, error in failed_files[:5]:  # Show first 5
                rel_path = filepath.relative_to(self.root_path)
                self.issues.append(f"Compilation error in {rel_path}: {error}")
                
    def check_test_discovery(self):
        """Check if tests can be discovered"""
        print("\nChecking test discovery...")
        
        try:
            # Try to discover tests
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--collect-only', '-q'],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Count collected tests
                lines = result.stdout.strip().split('\n')
                test_count = len([l for l in lines if '::' in l])
                print(f"✓ Found {test_count} tests")
            else:
                print("✗ Test discovery failed")
                self.issues.append(f"Test discovery failed: {result.stderr}")
                
        except Exception as e:
            print("✗ Could not run test discovery")
            self.warnings.append(f"Test discovery error: {e}")
            
    def check_lingering_imports(self):
        """Check for any remaining imports of deleted modules"""
        print("\nChecking for lingering imports...")
        
        deleted_modules = [
            'agenticraft.fabric.unified',
            'agenticraft.fabric.unified_enhanced',
            'agenticraft.protocols.mcp.transport',
            'agenticraft.protocols.mcp.auth',
            'agenticraft.security.auth',
            'agenticraft.utils.config'
        ]
        
        found_imports = {}
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', 'refactoring_backup']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            
                        for module in deleted_modules:
                            if module in content:
                                if module not in found_imports:
                                    found_imports[module] = []
                                found_imports[module].append(filepath.relative_to(self.root_path))
                                
                    except:
                        pass
                        
        if not found_imports:
            print("✓ No lingering imports of deleted modules found")
        else:
            print(f"✗ Found imports of {len(found_imports)} deleted modules")
            for module, files in found_imports.items():
                self.issues.append(f"Module '{module}' still imported in {len(files)} files")
                
    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 60)
        print("VALIDATION REPORT")
        print("=" * 60)
        
        if not self.issues and not self.warnings:
            print("\n✅ All validation checks passed!")
            print("Your refactoring appears to be successful.")
        else:
            if self.issues:
                print(f"\n❌ Found {len(self.issues)} issues:")
                for issue in self.issues:
                    print(f"  - {issue}")
                    
            if self.warnings:
                print(f"\n⚠️  Found {len(self.warnings)} warnings:")
                for warning in self.warnings[:5]:  # Show first 5
                    print(f"  - {warning}")
                    
        print("\n" + "=" * 60)
        
    def run_all_checks(self):
        """Run all validation checks"""
        print("Running refactoring validation...\n")
        
        self.check_required_modules()
        self.find_circular_imports()
        self.validate_imports()
        self.check_test_discovery()
        self.check_lingering_imports()
        
        self.generate_report()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate AgentiCraft refactoring')
    parser.add_argument('--path', default='/Users/zahere/Desktop/TLV/agenticraft',
                       help='Path to AgentiCraft root directory')
    parser.add_argument('--post-refactor', action='store_true',
                       help='Run post-refactoring checks')
    
    args = parser.parse_args()
    
    validator = RefactoringValidator(args.path)
    
    if args.post_refactor:
        print("Running POST-REFACTORING validation\n")
    else:
        print("Running PRE-REFACTORING validation\n")
        
    validator.run_all_checks()

if __name__ == '__main__':
    main()
