# Refactoring Completion Plan

## Current Status
The refactoring is ~70% complete. The new architecture is in place but old files haven't been removed, creating confusion.

## Files to Consolidate
1. `fabric/unified.py` - Basic unified fabric implementation
2. `fabric/unified_enhanced.py` - Enhanced fabric with ACP/ANP + extensions
3. `fabric/agent.py` - New refactored UnifiedAgent (imports from unified.py at bottom)

## Step-by-Step Plan

### Phase 1: Reorganize Code
1. **Create shared types module** (`fabric/protocol_types.py`)
   - Move: ProtocolType, ProtocolCapability, UnifiedTool, IProtocolAdapter

2. **Consolidate adapters** (`fabric/adapters/protocol_adapters.py`)
   - Move: MCPAdapter, A2AAdapter, ACPAdapter, ANPAdapter
   - These should use the refactored base classes

3. **Create extensions module** (`fabric/extensions.py`)
   - Move: IProtocolExtension and all extension classes
   - MeshNetworkingExtension, ConsensusExtension, ReasoningTraceExtension

4. **Create legacy fabric** (`fabric/legacy.py`)
   - Move: UnifiedProtocolFabric, EnhancedUnifiedProtocolFabric
   - Add deprecation warnings
   - This provides backwards compatibility

### Phase 2: Clean Up
1. **Update fabric/agent.py**
   - Remove imports from unified.py at bottom
   - Import shared types from protocol_types.py if needed

2. **Update compatibility layer** (`fabric/compat/__init__.py`)
   - Point old imports to new locations
   - Add entries for unified.py and unified_enhanced.py

3. **Remove old files**
   - Delete fabric/unified.py
   - Delete fabric/unified_enhanced.py

### Phase 3: Update Tests
1. **Update test imports**
   - Change from unified_enhanced to new locations
   - Update test_enhanced_fabric.py
   - Update test_sdk_integration.py

2. **Run tests**
   - Fix any remaining import issues
   - Ensure backwards compatibility works

## Benefits
- Clean separation of concerns
- No duplicate code
- Clear migration path
- Maintains backwards compatibility
- Aligns with refactoring plan
