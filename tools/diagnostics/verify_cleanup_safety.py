#!/usr/bin/env python3
"""
Comprehensive verification script to ensure cleanup is safe and tests won't break.
This script:
1. Checks what redundant files actually exist
2. Analyzes test files for imports of files to be deleted
3. Suggests refactoring needed before cleanup
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

BASE_DIR = Path(__file__).parent

# Files and directories marked for deletion from REDUNDANT_FILES.md
REDUNDANT_DIRS = [
    "protocols/mcp/transport",
    "protocols/mcp/auth",
    "protocols/a2a/centralized",
    "protocols/a2a/decentralized", 
    "protocols/a2a/hybrid",
    "security/authentication",
    "security/authorization",
    "fabric/adapters",  # Note: Check if this has new adapters
    "protocols/base_backup",
    "protocols/bridges",
    "protocols/external",
    "core/streaming",
]

REDUNDANT_FILES = [
    "protocols/mcp/decorators.py",
    "security/auth.py",
    "fabric/unified.py",
    "fabric/unified_enhanced.py",
    "fabric/sdk_fabric.py",
    "fabric/adapters_base.py",
    "utils/config.py",
]


class CleanupVerifier:
    def __init__(self):
        self.base_dir = BASE_DIR
        self.existing_redundant = {"dirs": [], "files": []}
        self.test_imports = {}
        self.import_issues = []
        self.refactoring_suggestions = []
        
    def check_existing_redundant(self):
        """Check which redundant files/dirs actually exist."""
        print("🔍 Checking for existing redundant files...\n")
        
        # Check directories
        for dir_path in REDUNDANT_DIRS:
            full_path = self.base_dir / dir_path
            if full_path.exists():
                self.existing_redundant["dirs"].append(dir_path)
                print(f"✓ DIR:  {dir_path}")
                # Special check for fabric/adapters
                if dir_path == "fabric/adapters":
                    self._check_adapters_content(full_path)
        
        # Check files
        for file_path in REDUNDANT_FILES:
            full_path = self.base_dir / file_path
            if full_path.exists():
                self.existing_redundant["files"].append(file_path)
                print(f"✓ FILE: {file_path}")
        
        total = len(self.existing_redundant["dirs"]) + len(self.existing_redundant["files"])
        print(f"\nTotal redundant items found: {total}")
        
    def _check_adapters_content(self, adapters_path: Path):
        """Special check for fabric/adapters directory."""
        print(f"  ⚠️  Checking contents of {adapters_path.relative_to(self.base_dir)}:")
        for item in sorted(adapters_path.iterdir()):
            if item.is_file() and item.suffix == ".py":
                print(f"      • {item.name}")
                # Check if this is a new adapter that shouldn't be deleted
                if any(name in item.name for name in ["official", "sdk", "new"]):
                    self.refactoring_suggestions.append(
                        f"WARNING: {item.relative_to(self.base_dir)} might be a new adapter - verify before deletion"
                    )
    
    def analyze_test_imports(self):
        """Analyze test files for imports of redundant modules."""
        print("\n📋 Analyzing test imports...")
        
        test_dir = self.base_dir / "tests"
        if not test_dir.exists():
            print("❌ Tests directory not found!")
            return
        
        # Patterns to look for
        redundant_modules = self._get_redundant_import_patterns()
        
        for test_file in test_dir.rglob("*.py"):
            if test_file.name.startswith("__"):
                continue
                
            imports = self._extract_imports(test_file)
            problematic = []
            
            for imp in imports:
                for pattern in redundant_modules:
                    if pattern in imp:
                        problematic.append((imp, pattern))
            
            if problematic:
                self.test_imports[str(test_file.relative_to(self.base_dir))] = problematic
        
        if self.test_imports:
            print(f"\n⚠️  Found {len(self.test_imports)} test files with imports of redundant modules:")
            for test_file, imports in self.test_imports.items():
                print(f"\n  {test_file}:")
                for imp, pattern in imports:
                    print(f"    • {imp} (matches: {pattern})")
                    self._suggest_refactoring(imp, pattern)
    
    def _get_redundant_import_patterns(self) -> List[str]:
        """Get patterns for imports that will break after cleanup."""
        patterns = []
        
        # From directories
        for dir_path in self.existing_redundant["dirs"]:
            module_path = dir_path.replace("/", ".")
            patterns.append(f"agenticraft.{module_path}")
            patterns.append(f"from {module_path}")
            
        # From files
        for file_path in self.existing_redundant["files"]:
            if file_path.endswith(".py"):
                module_path = file_path[:-3].replace("/", ".")
                patterns.append(f"agenticraft.{module_path}")
                patterns.append(f"from {module_path}")
        
        # Special patterns
        patterns.extend([
            "fabric.unified",
            "fabric.unified_enhanced",
            "fabric.sdk_fabric",
            "fabric.adapters_base",
            "security.auth",
            "utils.config",
            "protocols.mcp.decorators",
            "protocols.mcp.transport",
            "protocols.mcp.auth",
            "security.authentication",
            "security.authorization",
        ])
        
        return patterns
    
    def _extract_imports(self, file_path: Path) -> List[str]:
        """Extract all imports from a Python file."""
        imports = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Simple regex for imports
            import_patterns = [
                r'from\s+(\S+)\s+import',
                r'import\s+(\S+)',
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)
                
        except Exception as e:
            print(f"    Error reading {file_path}: {e}")
        
        return imports
    
    def _suggest_refactoring(self, import_line: str, pattern: str):
        """Suggest how to refactor an import."""
        suggestions = {
            "protocols.mcp.transport": "Use agenticraft.core.transport instead",
            "protocols.mcp.auth": "Use agenticraft.core.auth instead",
            "security.auth": "Use agenticraft.core.auth instead",
            "security.authentication": "Use agenticraft.core.auth instead",
            "fabric.unified": "Use agenticraft.fabric.agent.UnifiedAgent instead",
            "fabric.unified_enhanced": "Use agenticraft.fabric.agent.UnifiedAgent with extensions",
            "fabric.sdk_fabric": "Use agenticraft.fabric.agent with SDK preferences",
            "utils.config": "Use agenticraft.core.config instead",
            "protocols.a2a.centralized": "Use agenticraft.core.patterns instead",
            "protocols.a2a.decentralized": "Use agenticraft.core.patterns instead",
            "fabric.adapters": "Check if using new adapters from fabric.adapters",
        }
        
        for key, suggestion in suggestions.items():
            if key in pattern:
                self.refactoring_suggestions.append(f"Refactor: {import_line} → {suggestion}")
                break
    
    def check_cross_references(self):
        """Check for cross-references between redundant files."""
        print("\n🔗 Checking cross-references between redundant files...")
        
        issues = []
        
        # Check if any non-redundant files import redundant ones
        for py_file in self.base_dir.rglob("*.py"):
            # Skip test files (already checked)
            if "test" in str(py_file):
                continue
                
            # Skip redundant files themselves
            rel_path = str(py_file.relative_to(self.base_dir))
            if any(rel_path.startswith(d) for d in self.existing_redundant["dirs"]):
                continue
            if rel_path in self.existing_redundant["files"]:
                continue
                
            # Check imports