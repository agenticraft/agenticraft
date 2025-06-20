# AgentiCraft Cleanup Scripts

## Overview

These scripts help safely remove redundant files after the AgentiCraft refactoring. The cleanup is based on the analysis in `REDUNDANT_FILES.md`.

## Scripts

### 1. `cleanup_check.py` - Safety Check Script
Run this FIRST to ensure it's safe to proceed with cleanup.

```bash
python cleanup_check.py
```

This script checks:
- ✅ Git working directory is clean (no uncommitted changes)
- ✅ No active imports of files to be deleted
- ✅ Tests are passing (or only have expected import errors)
- ✅ Backup directory can be created

### 2. `cleanup_redundant_files.py` - Main Cleanup Script

#### Dry Run (Default)
See what will be deleted without actually deleting:
```bash
python cleanup_redundant_files.py
```

#### Execute Cleanup
Actually delete the redundant files:
```bash
python cleanup_redundant_files.py --execute
```

#### Skip Review Items
Don't show files that need manual review:
```bash
python cleanup_redundant_files.py --skip-review
```

## What Gets Deleted

### Directories (12 total)
- Protocol transport/auth duplicates that moved to core
- Old adapter patterns replaced by unified agent
- Empty backup directories
- Legacy protocol bridges

### Files (7 total)
- Old fabric implementations (unified.py, etc.)
- Duplicate auth and config files
- Legacy decorators

### Total: ~50 files, freeing several MB

## Safety Features

1. **Dry Run by Default** - Nothing deleted without explicit --execute flag
2. **Backup Manifest** - JSON record of all deletions with timestamps
3. **Rollback Script** - Generated script showing how to restore files
4. **Git Safety** - Won't run if you have uncommitted changes
5. **Confirmation Required** - Must type "yes" to proceed with deletion

## Cleanup Process

### Step 1: Run Safety Check
```bash
python cleanup_check.py
```

### Step 2: Review What Will Be Deleted
```bash
python cleanup_redundant_files.py
```

### Step 3: Commit Current Work
```bash
git add .
git commit -m "Pre-cleanup checkpoint"
```

### Step 4: Execute Cleanup
```bash
python cleanup_redundant_files.py --execute
# Type 'yes' when prompted
```

### Step 5: Verify and Commit
```bash
# Run tests
pytest tests/

# If all good, commit the cleanup
git add .
git commit -m "Remove redundant files after refactoring"
```

## Recovery

If you need to restore deleted files:

### Option 1: Use Git
```bash
# Restore specific file
git checkout HEAD~ -- path/to/deleted/file.py

# Or restore all deleted files
git checkout HEAD~
```

### Option 2: Check Rollback Script
Look in `cleanup_backups/` for the rollback script with instructions.

## Files That Need Review

The following require manual review before deletion:
- `agents/patterns/` - Check for unique patterns vs `/core/patterns/`
- `security/middleware.py` - Might have useful middleware
- `security/sandbox/` - Sandboxing functionality
- `security/audit/` - Audit logging

Review these manually and either:
1. Move useful code to appropriate locations
2. Delete if truly redundant
3. Keep if still needed

## Troubleshooting

### "Git working directory not clean"
Commit or stash your changes first:
```bash
git stash  # or git commit
```

### "Import errors found"
Some files still import redundant modules. Update imports first or verify they're in test files that will be updated.

### "Tests failing"
If tests fail for reasons other than imports, fix them before cleanup.

### Already cleaned up?
If you see "No redundant files found!", the cleanup was already performed.

## Questions?

- Check `REDUNDANT_FILES.md` for rationale
- Check `REFACTORING_SUMMARY.md` for architecture overview
- Review git history to see what was moved where
