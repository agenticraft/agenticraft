# Redundant Files After Refactoring

## Protocol-Related Redundancies

### MCP Protocol
- `/protocols/mcp/transport/` (entire directory) - Replaced by `/core/transport/`
  - `base.py`
  - `http.py` 
  - `websocket.py`

- `/protocols/mcp/auth/` (entire directory) - Replaced by `/core/auth/`
  - `api_key.py`
  - `bearer.py`
  - `hmac.py`
  - `jwt.py`

- `/protocols/mcp/decorators.py` - Functionality moved to core or no longer needed

### A2A Protocol  
- Old pattern implementations that are now in `/core/patterns/`:
  - `/protocols/a2a/centralized/` - Replaced by core patterns
  - `/protocols/a2a/decentralized/` - Replaced by core patterns
  - `/protocols/a2a/hybrid/` - Replaced by core patterns

## Security Module Redundancies
- `/security/authentication/` - Replaced by `/core/auth/`
  - `api_key.py`
  - `jwt.py`

- `/security/authorization/` - Can be moved to core auth if needed
  - `permissions.py`
  - `rbac.py`

- `/security/auth.py` - Replaced by `/core/auth/`

## Fabric Redundancies
After the unified agent approach:

- `/fabric/adapters/` - These adapter patterns are replaced by the unified agent:
  - `a2a_adapter.py`
  - `mcp_adapter.py`
  - `adapter_factory.py`

- Duplicate/experimental fabric implementations:
  - `/fabric/unified.py` - Replaced by the refactored `/fabric/agent.py`
  - `/fabric/unified_enhanced.py` - Experimental, replaced by current implementation
  - `/fabric/sdk_fabric.py` - SDK-specific, replaced by unified approach
  - `/fabric/adapters_base.py` - No longer needed with new architecture

## Configuration Redundancies
- `/utils/config.py` - Replaced by `/core/config.py`

## Other Redundancies
- `/protocols/base_backup/` - Empty backup directory
- `/protocols/bridges/` - Protocol bridging now handled by unified agent
- `/protocols/external/` - External protocol support now in unified fabric

- `/core/streaming/` (empty directory) - Functionality in `/core/streaming.py`

- Agent pattern duplicates:
  - `/agents/patterns/` - Some patterns may duplicate `/core/patterns/`
  - Review individually to see which are still needed

## Summary of Deletions

### Entire Directories to Delete:
1. `/protocols/mcp/transport/`
2. `/protocols/mcp/auth/`
3. `/protocols/a2a/centralized/`
4. `/protocols/a2a/decentralized/`
5. `/protocols/a2a/hybrid/`
6. `/security/authentication/`
7. `/security/authorization/`
8. `/fabric/adapters/`
9. `/protocols/base_backup/`
10. `/protocols/bridges/`
11. `/protocols/external/`
12. `/core/streaming/` (empty)

### Individual Files to Delete:
1. `/protocols/mcp/decorators.py`
2. `/security/auth.py`
3. `/fabric/unified.py`
4. `/fabric/unified_enhanced.py`
5. `/fabric/sdk_fabric.py`
6. `/fabric/adapters_base.py`
7. `/utils/config.py`

## Files to Review Before Deletion
These might have unique functionality to preserve:

1. `/agents/patterns/` - Check if any patterns are unique vs `/core/patterns/`
2. `/security/middleware.py` - Might have useful middleware to move to core
3. `/security/sandbox/` - Sandboxing functionality might be useful to keep
4. `/security/audit/` - Audit logging might be useful to move to core

## Migration Notes

Before deleting, ensure:
1. All tests are updated to use new imports
2. Examples are updated to use new architecture
3. Documentation reflects the new structure
4. Any unique functionality is preserved in the new architecture

The refactored architecture is cleaner with:
- Centralized auth in `/core/auth/`
- Centralized transport in `/core/transport/`
- Unified agent interface in `/fabric/agent.py`
- Protocol implementations using core abstractions
