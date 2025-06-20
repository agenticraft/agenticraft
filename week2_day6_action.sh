#!/bin/bash
# Week 2 Day 6: Start Module Consolidation

echo "🚀 Week 2 Day 6: Module Consolidation"
echo "====================================="

# Create Week 2 branch
echo -e "\n📌 Creating Week 2 branch..."
git checkout -b week2-consolidation 2>/dev/null || {
    echo "Already on week2-consolidation branch"
}

# Commit current state
echo -e "\n💾 Saving current state..."
git add -A
git commit -m "chore: Week 2 start - 835 tests passing" 2>/dev/null || {
    echo "Nothing to commit"
}

# Step 1: Fix easy test issues first
echo -e "\n1️⃣ Fixing Easy Test Issues (should fix ~10 tests)..."
chmod +x fix_easy_test_issues.sh
./fix_easy_test_issues.sh

# Quick test to see improvement
echo -e "\n📊 Quick test check..."
pytest tests/test_structure.py -v --tb=short 2>&1 | grep -E "(PASSED|FAILED|ERROR)" | tail -5

# Step 2: Create new directory structure
echo -e "\n2️⃣ Creating New Directory Structure..."
chmod +x create_week2_structure.sh
./create_week2_structure.sh

# Step 3: Analyze what needs to be moved
echo -e "\n3️⃣ Analyzing Modules to Move..."
chmod +x analyze_modules_to_move.sh
./analyze_modules_to_move.sh > module_analysis.txt
echo "Analysis saved to module_analysis.txt"

# Show summary
echo -e "\n📊 Module Summary:"
grep -E "files\)|modules:" module_analysis.txt | head -10

# Step 4: Move experimental modules
echo -e "\n4️⃣ Ready to Move Modules?"
echo "This will:"
echo "- Move protocols to experimental/protocols"
echo "- Move fabric to experimental/fabric"  
echo "- Move marketplace to experimental/marketplace"
echo "- Update all imports automatically"
echo ""
read -p "Continue with module migration? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    chmod +x move_experimental_modules.sh
    ./move_experimental_modules.sh
    
    # Test after move
    echo -e "\n🧪 Testing core modules after move..."
    pytest tests/unit/core -v --tb=short -x 2>&1 | tail -20
else
    echo "Skipping module migration for now"
fi

# Step 5: Create simplified public API
echo -e "\n5️⃣ Creating Simplified Public API..."
cat > agenticraft/__init__.py.new << 'EOF'
"""AgentiCraft - Multi-Provider AI Agent Framework.

Simple, clean public API for building AI agents.
"""

__version__ = "0.2.0"

# Core imports - these are stable
from agenticraft.core.agent import Agent
from agenticraft.core.tool import Tool, tool
from agenticraft.core.workflow import WorkflowAgent, Workflow

# Stable providers
from agenticraft.providers import (
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
)

# Main exports - single import interface
__all__ = [
    # Core classes
    "Agent",
    "Tool", 
    "tool",
    "WorkflowAgent",
    "Workflow",
    # Providers
    "OpenAIProvider",
    "AnthropicProvider", 
    "OllamaProvider",
    # Version
    "__version__",
]

# Compatibility attributes
class _ProtocolsModule:
    """Compatibility wrapper for protocols."""
    def __getattr__(self, name):
        import warnings
        warnings.warn(
            "agenticraft.protocols is deprecated. Use agenticraft.experimental.protocols",
            DeprecationWarning,
            stacklevel=2
        )
        from agenticraft.experimental import protocols
        return getattr(protocols, name)

protocols = _ProtocolsModule()

# Simplified configuration
def configure(**kwargs):
    """Simple configuration helper."""
    from agenticraft.utils.config import Config
    return Config(**kwargs)
EOF

echo "✅ New simplified API created (saved as __init__.py.new)"
echo "   Review and apply with: mv agenticraft/__init__.py.new agenticraft/__init__.py"

# Summary
echo -e "\n📊 Day 6 Progress Summary:"
echo "======================================"
echo "✅ Fixed easy test issues"
echo "✅ Created new directory structure"
echo "✅ Analyzed modules to move"
echo "🔄 Module migration (if confirmed)"
echo "✅ Designed simplified public API"

echo -e "\n🎯 Day 6 Success Metrics:"
# Count current test status
if [ -f "test_full_report.txt" ]; then
    passed=$(grep -c "PASSED" test_full_report.txt 2>/dev/null || echo "0")
    failed=$(grep -c "FAILED" test_full_report.txt 2>/dev/null || echo "0")
    echo "Tests: $passed passed, $failed failed (was 835/23)"
fi

echo -e "\n💡 Next Steps for Day 7:"
echo "1. Complete module migration if not done"
echo "2. Consolidate utility modules"
echo "3. Update all imports"
echo "4. Run full test suite"
echo "5. Fix any broken tests"

echo -e "\n📝 To check current status:"
echo "pytest tests/ -v --tb=short -k 'not telemetry' | grep -E '(passed|failed|ERROR)' | tail -20"