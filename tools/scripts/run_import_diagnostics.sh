#!/bin/bash
# Run import diagnostics

echo "🔍 Running Import System Diagnostics..."
echo "====================================="
echo ""

# Change to project directory
cd /Users/zahere/Desktop/TLV/agenticraft

# Check for quick mode (default) or full mode
MODE=${1:-quick}

if [ "$MODE" = "quick" ]; then
    echo "Running QUICK diagnostics (core modules only)"
    echo "For full scan including all files, run: $0 full"
    echo ""
    
    # Quick import check
    echo "1. Quick import check..."
    echo "----------------------"
    python tools/diagnostics/quick_import_check.py
    echo ""
else
    echo "Running FULL diagnostics (this may take a while)"
    echo ""
    
    # 1. Run comprehensive import audit
    echo "1. Running comprehensive import audit..."
    echo "---------------------------------------"
    python tools/diagnostics/import_audit.py
    echo ""
fi

# 2. Check for redundant imports
echo "2. Checking for redundant imports..."
echo "-----------------------------------"
python tools/diagnostics/check_redundant_imports.py
echo ""

# 3. Verify specific imports
echo "3. Verifying specific imports..."
echo "-------------------------------"
python tools/diagnostics/verify_all_imports.py
echo ""

# 4. Quick test of main package import
echo "4. Testing main package import..."
echo "--------------------------------"
python -c "
try:
    import agenticraft
    print('✅ Main package imports successfully')
    print(f'   Version: {agenticraft.__version__}')
    print(f'   Location: {agenticraft.__file__}')
except Exception as e:
    print(f'❌ Main package import failed: {e}')
"
echo ""

# 5. Test core module imports
echo "5. Testing core module imports..."
echo "--------------------------------"
python -c "
errors = []
modules = [
    'agenticraft.core.agent',
    'agenticraft.core.tool',
    'agenticraft.core.workflow',
    'agenticraft.core.exceptions',
    'agenticraft.agents',
    'agenticraft.providers',
    'agenticraft.workflows'
]

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
        errors.append(module)

if not errors:
    print('\\n✅ All core modules import successfully!')
else:
    print(f'\\n❌ {len(errors)} modules failed to import')
"

echo ""
echo "Diagnostics complete!"
