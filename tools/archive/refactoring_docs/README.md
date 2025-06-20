# AgentiCraft Refactoring Tools

This directory contains scripts to help refactor AgentiCraft by removing redundant modules and updating imports.

## Quick Start

1. **Check current status:**
   ```bash
   python check_status.py
   ```

2. **Validate before starting:**
   ```bash
   python validate_refactoring.py
   ```

3. **Update imports (dry run):**
   ```bash
   python update_imports.py
   ```

4. **Update imports (apply):**
   ```bash
   python update_imports.py --apply
   ```

5. **Delete safe modules:**
   ```bash
   python delete_redundant_modules.py --quick --execute
   ```

6. **Validate after refactoring:**
   ```bash
   python validate_refactoring.py --post-refactor
   ```

## Scripts

- **check_status.py** - Quick overview of refactoring progress
- **update_imports.py** - Updates all imports from old to new modules
- **delete_redundant_modules.py** - Safely deletes modules that are no longer used
- **validate_refactoring.py** - Validates the codebase before/after refactoring

## Full Guide

See [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) for detailed instructions.

## Safety

- All scripts create backups before making changes
- Run in dry-run mode first to preview changes
- Validate after each major step
