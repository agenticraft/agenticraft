#!/usr/bin/env python3
"""
Update tests to align with the refactored structure.
This script:
1. Identifies test files with outdated imports
2. Updates them to use the new structure
3. Creates a backup before modifying
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).parent


class TestRefactorer:
    def __init__(self, dry_run: bool = True):
        self.base_dir = BASE_DIR
        self.dry_run = dry_run
        self.backup_dir = self.base_dir / "test_refactor_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.changes_made = []
        
        # Define import mappings from old to new
        self.import_mappings = {
            # Old unified modules -> new locations
            r"from agenticraft\.fabric\.unified import (.+)": 
                "from agenticraft.fabric import \\1",
            
            r"from agenticraft\.fabric\.unified_enhanced import (.+)": 
                "from agenticraft.fabric import \\1",
            
            r"from agenticraft\.fabric\.sdk_fabric import (.+)":
                "from agenticraft.fabric import \\1",
            
            # Old auth location -> new location
            r"from agenticraft\.security\.auth import (.+)":
                "from agenticraft.core.auth import \\1",
            
            # Old config location -> new location  
            r"from agenticraft\.utils\.config import (.+)":
                "from agenticraft.core.config import \\1",
            
            # Protocol types from wrong location
            r"from agenticraft\.fabric\.agent_enhanced import ProtocolType":
                "from agenticraft.fabric import ProtocolType",
            
            r"from agenticraft\.fabric\.agent_enhanced import (.+)":
                "from agenticraft.fabric.protocol_types import \\1",
            
            # Import entire modules
            r"import agenticraft\.fabric\.unified\b":
                "import agenticraft.fabric",
            
            r"import agenticraft\.fabric\.unified_enhanced\b":
                "import agenticraft.fabric",
            
            # Special cases for test-specific imports
            r"from agenticraft\.fabric\.adapters import ProtocolAdapter":
                "from agenticraft.fabric.adapters import ProtocolAdapter",
            
            r"from agenticraft\.fabric\.adapters import AdapterRegistry":
                "from agenticraft.fabric.adapters import AdapterRegistry",
        }
        
        # Additional specific replacements
        self.specific_replacements = {
            # Class name changes if any
            "UnifiedFabric": "UnifiedProtocolFabric",
            "create_sdk_agent": "create_mcp_agent",  # If this was renamed
        }
    
    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of a file before modifying."""
        if not self.dry_run:
            rel_path = file_path.relative_to(self.base_dir)
            backup_path = self.backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return backup_path
        return file_path
    
    def update_imports_in_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """Update imports in a single file."""
        changes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = original_content = f.read()
            
            # Apply import mappings
            for old_pattern, new_pattern in self.import_mappings.items():
                if re.search(old_pattern, content):
                    new_content = re.sub(old_pattern, new_pattern, content)
                    if new_content != content:
                        changes.append((old_pattern, new_pattern))
                        content = new_content
            
            # Apply specific replacements
            for old_name, new_name in self.specific_replacements.items():
                if old_name in content:
                    # Only replace if it's not part of another word
                    pattern = r'\b' + re.escape(old_name) + r'\b'
                    new_content = re.sub(pattern, new_name, content)
                    if new_content != content:
                        changes.append((old_name, new_name))
                        content = new_content
            
            # Write changes if any were made
            if changes and content != original_content:
                if not self.dry_run:
                    self.backup_file(file_path)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                self.changes_made.append((file_path, changes))
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
        
        return changes
    
    def find_test_files(self) -> List[Path]:
        """Find all test files."""
        test_files = []
        test_dir = self.base_dir / "tests"
        
        if test_dir.exists():
            for test_file in test_dir.rglob("test_*.py"):
                test_files.append(test_file)
        
        # Also check for test files in the main directory
        for test_file in self.base_dir.glob("test_*.py"):
            test_files.append(test_file)
        
        return test_files
    
    def update_conftest_files(self) -> None:
        """Update conftest.py files if needed."""
        for conftest in self.base_dir.rglob("conftest.py"):
            self.update_imports_in_file(conftest)
    
    def run_refactoring(self) -> None:
        """Run the test refactoring process."""
        print("=" * 80)
        print(f"TEST REFACTORING {'(DRY RUN)' if self.dry_run else ''}")
        print("=" * 80)
        
        # Find test files
        test_files = self.find_test_files()
        print(f"\nFound {len(test_files)} test files")
        
        # Update imports in each file
        for test_file in test_files:
            changes = self.update_imports_in_file(test_file)
            if changes:
                print(f"\n📝 {test_file.relative_to(self.base_dir)}:")
                for old, new in changes:
                    print(f"  • {old} → {new}")
        
        # Update conftest files
        self.update_conftest_files()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if self.changes_made:
            print(f"\n{'Would update' if self.dry_run else 'Updated'} {len(self.changes_made)} files:")
            for file_path, changes in self.changes_made:
                rel_path = file_path.relative_to(self.base_dir)
                print(f"\n  {rel_path}:")
                print(f"    {len(changes)} import{'s' if len(changes) > 1 else ''} updated")
            
            if not self.dry_run:
                print(f"\n✅ Backups saved to: {self.backup_dir}")
        else:
            print("\n✅ No test files need updating - all imports are already correct!")
    
    def create_update_script(self) -> None:
        """Create a script to apply specific updates."""
        script_path = self.base_dir / "apply_test_updates.py"
        
        script_content = '''#!/usr/bin/env python3
"""
Apply specific test updates based on refactoring analysis.
Auto-generated script to update test imports.
"""

import re
from pathlib import Path

updates = [
'''
        
        # Add specific updates found
        for file_path, changes in self.changes_made:
            rel_path = file_path.relative_to(self.base_dir)
            script_content += f'    ("{rel_path}", [\n'
            for old, new in changes:
                script_content += f'        ({repr(old)}, {repr(new)}),\n'
            script_content += '    ]),\n'
        
        script_content += ''']

def apply_updates():
    """Apply the updates to test files."""
    for file_path, replacements in updates:
        path = Path(file_path)
        if path.exists():
            with open(path, 'r') as f:
                content = f.read()
            
            for old, new in replacements:
                content = re.sub(old, new, content)
            
            with open(path, 'w') as f:
                f.write(content)
            
            print(f"Updated: {file_path}")

if __name__ == "__main__":
    apply_updates()
'''
        
        if self.changes_made and not self.dry_run:
            with open(script_path, 'w') as f:
                f.write(script_content)
            script_path.chmod(0o755)
            print(f"\n📄 Update script created: {script_path}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update test files to align with refactored structure"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually update files (default is dry run)"
    )
    parser.add_argument(
        "--create-script",
        action="store_true",
        help="Create a script with specific updates"
    )
    
    args = parser.parse_args()
    
    refactorer = TestRefactorer(dry_run=not args.execute)
    refactorer.run_refactoring()
    
    if args.create_script:
        refactorer.create_update_script()
    
    if not args.execute:
        print("\n💡 To apply changes, run with --execute flag:")
        print(f"   python {Path(__file__).name} --execute")


if __name__ == "__main__":
    main()
