# AgentiCraft Refactoring Guide

## Overview
This guide helps you safely refactor AgentiCraft by removing redundant modules and updating imports throughout the codebase.

## Current Status

### Redundant Modules Identified
- **68 imports** across **28 files** need updating
- **7 modules** appear safe to delete immediately (no imports found)
- **8 modules** still have active imports that need migration

### Safe to Delete (No Imports)
1. `agenticraft/fabric/adapters_base.py`
2. `agenticraft/protocols/mcp/transport/`
3. `agenticraft/protocols/bridges/`
4. `agenticraft/security/authentication/`
5. `agenticraft/security/authorization/`
6. `agenticraft/security/auth.py`
7. `agenticraft/utils/config.py`

### Requires Migration First
1. `agenticraft/fabric/unified.py` (29 imports)
2. `agenticraft/fabric/unified_enhanced.py` (24 imports)
3. `agenticraft/fabric/sdk_fabric.py` (2 imports)
4. `agenticraft/protocols/mcp/auth/` (3 imports)
5. `agenticraft/protocols/a2a/centralized/` (2 imports)
6. `agenticraft/protocols/a2a/decentralized/` (2 imports)
7. `agenticraft/protocols/a2a/hybrid/` (4 imports)
8. `agenticraft/protocols/external/` (6 imports)

## Refactoring Process

### Phase 1: Preparation
1. **Create backup** of your entire project
2. **Ensure all tests pass** before starting
3. **Verify target modules exist**:
   ```bash
   cd /Users/zahere/Desktop/TLV/agenticraft
   python refactoring_tools/update_imports.py --verify-only
   ```

### Phase 2: Update Imports

1. **Dry run** to see what will change:
   ```bash
   python refactoring_tools/update_imports.py
   ```

2. **Apply import updates**:
   ```bash
   python refactoring_tools/update_imports.py --apply
   ```

3. **Run tests** to ensure nothing broke

### Phase 3: Delete Safe Modules

1. **Quick analysis** of safe modules:
   ```bash
   python refactoring_tools/delete_redundant_modules.py --quick
   ```

2. **Delete safe modules**:
   ```bash
   python refactoring_tools/delete_redundant_modules.py --quick --execute
   ```

### Phase 4: Handle Remaining Modules

1. **Full analysis** to see what's left:
   ```bash
   python refactoring_tools/delete_redundant_modules.py
   ```

2. **Review migration report** at `refactoring_tools/migration_needed.txt`

3. **Manual updates** may be needed for complex cases

### Phase 5: Final Cleanup

1. **Run all tests** again
2. **Check for broken imports**:
   ```bash
   python -m py_compile agenticraft/**/*.py
   ```
3. **Remove backup** once confirmed working

## Import Mappings

| Old Import | New Import |
|------------|------------|
| `agenticraft.protocols.mcp.transport` | `agenticraft.core.transport` |
| `agenticraft.protocols.mcp.auth` | `agenticraft.core.auth` |
| `agenticraft.security.auth` | `agenticraft.core.auth` |
| `agenticraft.security.authentication` | `agenticraft.core.auth` |
| `agenticraft.security.authorization` | `agenticraft.core.auth` |
| `agenticraft.utils.config` | `agenticraft.core.config` |
| `agenticraft.fabric.unified` | `agenticraft.fabric.agent` |
| `agenticraft.fabric.unified_enhanced` | `agenticraft.fabric.agent` |

## Troubleshooting

### Import Not Found Errors
- Ensure target modules exist before updating imports
- Check if the module needs a different mapping than listed above

### Test Failures
- Review the backup to see original import structure
- Some imports may need manual adjustment based on what was imported

### Circular Import Issues
- May need to restructure some modules if circular dependencies emerge
- Consider using TYPE_CHECKING imports for type hints

## Recovery

If something goes wrong:
1. Backups are created at `refactoring_backup/[timestamp]/`
2. Import updates create `.backup` files
3. Use git to revert changes if needed

## Next Steps

After completing the refactoring:
1. Update documentation to reflect new module structure
2. Update import statements in example code
3. Consider adding import deprecation warnings for a transition period
4. Update CI/CD configurations if module paths are referenced

## Notes

- The `fabric.unified` → `fabric.agent` migration has the most imports (29)
- Pay special attention to `unified_enhanced` imports as they may need careful mapping
- Some modules like `adapters` may need special handling due to submodule imports
