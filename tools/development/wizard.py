#!/usr/bin/env python3
"""
Interactive refactoring wizard for AgentiCraft
Guides through the refactoring process step by step
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

class RefactoringWizard:
    def __init__(self):
        self.root_path = Path('/Users/zahere/Desktop/TLV/agenticraft')
        self.scripts_dir = self.root_path / 'refactoring_tools'
        self.step = 1
        
    def run_command(self, cmd: list) -> tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
            
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"Step {self.step}: {title}")
        print("=" * 60)
        self.step += 1
        
    def prompt_continue(self, message: str = "Continue?") -> bool:
        """Prompt user to continue"""
        response = input(f"\n{message} (y/n): ").lower()
        return response == 'y'
        
    def run_status_check(self):
        """Run status check"""
        self.print_header("Current Status")
        success, output = self.run_command([
            sys.executable, 
            str(self.scripts_dir / 'check_status.py')
        ])
        print(output)
        return success
        
    def run_pre_validation(self):
        """Run pre-refactoring validation"""
        self.print_header("Pre-Refactoring Validation")
        
        if not self.prompt_continue("Run validation checks?"):
            return False
            
        success, output = self.run_command([
            sys.executable,
            str(self.scripts_dir / 'validate_refactoring.py')
        ])
        print(output)
        
        if not success:
            print("\n⚠️  Validation found issues. Review and fix before continuing.")
            return False
            
        return True
        
    def update_imports(self):
        """Update imports across the codebase"""
        self.print_header("Update Imports")
        
        # First do a dry run
        print("Running dry run to preview changes...\n")
        success, output = self.run_command([
            sys.executable,
            str(self.scripts_dir / 'update_imports.py')
        ])
        
        # Show only summary
        lines = output.split('\n')
        summary_start = False
        for line in lines:
            if 'SUMMARY REPORT' in line:
                summary_start = True
            if summary_start:
                print(line)
                
        if not self.prompt_continue("\nApply these import updates?"):
            return False
            
        # Apply changes
        print("\nApplying import updates...")
        success, output = self.run_command([
            sys.executable,
            str(self.scripts_dir / 'update_imports.py'),
            '--apply'
        ])
        
        if success:
            print("✓ Import updates applied successfully")
        else:
            print("✗ Import updates failed")
            print(output)
            
        return success
        
    def delete_safe_modules(self):
        """Delete modules that have no imports"""
        self.print_header("Delete Safe Modules")
        
        # First show what's safe to delete
        print("Analyzing modules marked as safe...\n")
        success, output = self.run_command([
            sys.executable,
            str(self.scripts_dir / 'delete_redundant_modules.py'),
            '--quick'
        ])
        
        # Extract safe modules from output
        safe_count = output.count('SAFE TO DELETE')
        
        if safe_count == 0:
            print("No modules are currently safe to delete.")
            return True
            
        print(f"\nFound {safe_count} modules safe to delete.")
        
        if not self.prompt_continue("Delete these modules?"):
            return False
            
        # Delete modules
        print("\nDeleting safe modules...")
        success, output = self.run_command([
            sys.executable,
            str(self.scripts_dir / 'delete_redundant_modules.py'),
            '--quick',
            '--execute'
        ])
        
        if success:
            print("✓ Safe modules deleted successfully")
        else:
            print("✗ Module deletion failed")
            
        return success
        
    def analyze_remaining(self):
        """Analyze remaining modules"""
        self.print_header("Analyze Remaining Modules")
        
        success, output = self.run_command([
            sys.executable,
            str(self.scripts_dir / 'delete_redundant_modules.py')
        ])
        
        # Count remaining modules with imports
        import_count = output.count('STILL HAS')
        
        if import_count > 0:
            print(f"\n⚠️  {import_count} modules still have active imports")
            print("These need manual review and migration.")
            print("\nCheck 'refactoring_tools/migration_needed.txt' for details")
        else:
            print("\n✓ All redundant modules have been processed!")
            
        return True
        
    def run_post_validation(self):
        """Run post-refactoring validation"""
        self.print_header("Post-Refactoring Validation")
        
        if not self.prompt_continue("Run final validation?"):
            return False
            
        success, output = self.run_command([
            sys.executable,
            str(self.scripts_dir / 'validate_refactoring.py'),
            '--post-refactor'
        ])
        print(output)
        
        return success
        
    def run_tests(self):
        """Attempt to run tests"""
        self.print_header("Run Tests")
        
        if not self.prompt_continue("Run test suite?"):
            return False
            
        print("Running tests...")
        success, output = self.run_command([
            sys.executable,
            '-m',
            'pytest',
            '-v',
            '--tb=short'
        ])
        
        if success:
            print("\n✓ All tests passed!")
        else:
            print("\n✗ Some tests failed. Review and fix issues.")
            
        return success
        
    def cleanup(self):
        """Cleanup backup files"""
        self.print_header("Cleanup")
        
        # Find backup files
        backup_files = list(self.root_path.rglob("*.py.backup"))
        
        if not backup_files:
            print("No backup files to clean up.")
            return True
            
        print(f"Found {len(backup_files)} backup files.")
        
        if not self.prompt_continue("Delete backup files?"):
            print("Keeping backup files.")
            return True
            
        for backup in backup_files:
            backup.unlink()
            
        print(f"✓ Deleted {len(backup_files)} backup files")
        return True
        
    def run(self):
        """Run the complete wizard"""
        print("🧙 AgentiCraft Refactoring Wizard")
        print("=" * 60)
        print("This wizard will guide you through the refactoring process.")
        print("You can stop at any time by pressing Ctrl+C")
        
        try:
            # Step 1: Status check
            if not self.run_status_check():
                return
                
            # Step 2: Pre-validation
            if not self.run_pre_validation():
                if not self.prompt_continue("Continue anyway?"):
                    return
                    
            # Step 3: Update imports
            if not self.update_imports():
                print("\n❌ Import update failed. Please fix issues and try again.")
                return
                
            # Step 4: Delete safe modules
            if not self.delete_safe_modules():
                print("\n❌ Module deletion failed.")
                return
                
            # Step 5: Analyze remaining
            self.analyze_remaining()
            
            # Step 6: Post-validation
            self.run_post_validation()
            
            # Step 7: Run tests
            self.run_tests()
            
            # Step 8: Cleanup
            if self.prompt_continue("\nRefactoring complete! Clean up backup files?"):
                self.cleanup()
                
            print("\n" + "=" * 60)
            print("✅ Refactoring wizard completed!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Review any remaining modules that need manual migration")
            print("2. Update documentation to reflect new module structure")
            print("3. Commit your changes to version control")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Wizard interrupted by user")
            print("You can resume by running the wizard again")

def main():
    wizard = RefactoringWizard()
    wizard.run()

if __name__ == '__main__':
    main()
