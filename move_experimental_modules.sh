#!/bin/bash
# Move experimental modules to the new structure

echo "🚀 Moving Experimental Modules - Week 2"
echo "======================================"

# Safety check
if [ ! -d "agenticraft/experimental" ]; then
    echo "❌ Error: experimental directory not found. Run create_week2_structure.sh first!"
    exit 1
fi

# Create backup
echo -e "\n💾 Creating backup..."
cp -r agenticraft agenticraft_backup_week2
echo "✅ Backup created at agenticraft_backup_week2/"

# Function to safely move files
safe_move() {
    source=$1
    dest=$2
    if [ -e "$source" ]; then
        echo "  Moving: $source → $dest"
        mv "$source" "$dest"
    fi
}

# Function to update imports in a file
update_imports() {
    file=$1
    echo "  Updating imports in: $file"
    
    # Update protocol imports
    sed -i.bak 's/from agenticraft\.protocols/from agenticraft.experimental.protocols/g' "$file"
    sed -i.bak 's/from agenticraft\.mcp/from agenticraft.experimental.protocols.mcp/g' "$file"
    sed -i.bak 's/from agenticraft\.a2a/from agenticraft.experimental.protocols.a2a/g' "$file"
    
    # Update fabric imports
    sed -i.bak 's/from agenticraft\.fabric/from agenticraft.experimental.fabric/g' "$file"
    
    # Update marketplace imports
    sed -i.bak 's/from agenticraft\.marketplace/from agenticraft.experimental.marketplace/g' "$file"
    
    # Clean up backup files
    rm -f "${file}.bak"
}

echo -e "\n1️⃣ Moving Protocol Modules..."
echo "----------------------------------------"

# Move MCP-related files
if [ -d "agenticraft/mcp" ]; then
    echo "Moving MCP directory..."
    mv agenticraft/mcp agenticraft/experimental/protocols/
fi

# Move individual protocol files
for file in agenticraft/*mcp*.py agenticraft/*a2a*.py agenticraft/*protocol*.py; do
    if [ -f "$file" ] && [[ ! "$file" =~ "__pycache__" ]]; then
        basename=$(basename "$file")
        safe_move "$file" "agenticraft/experimental/protocols/$basename"
    fi
done

# Move protocols directory if it exists
if [ -d "agenticraft/protocols" ]; then
    echo "Moving protocols directory contents..."
    cp -r agenticraft/protocols/* agenticraft/experimental/protocols/ 2>/dev/null
    rm -rf agenticraft/protocols
fi

echo -e "\n2️⃣ Moving Fabric Modules..."
echo "----------------------------------------"

if [ -d "agenticraft/fabric" ]; then
    echo "Moving fabric directory contents..."
    # Keep __init__.py in experimental/fabric
    mv agenticraft/fabric/* agenticraft/experimental/fabric/ 2>/dev/null
    rmdir agenticraft/fabric 2>/dev/null
fi

echo -e "\n3️⃣ Moving Marketplace Modules..."
echo "----------------------------------------"

# Move marketplace directory if exists
if [ -d "agenticraft/marketplace" ]; then
    echo "Moving marketplace directory..."
    mv agenticraft/marketplace/* agenticraft/experimental/marketplace/ 2>/dev/null
    rmdir agenticraft/marketplace
fi

# Move individual marketplace files
for file in agenticraft/*marketplace*.py; do
    if [ -f "$file" ] && [[ ! "$file" =~ "__pycache__" ]]; then
        basename=$(basename "$file")
        safe_move "$file" "agenticraft/experimental/marketplace/$basename"
    fi
done

echo -e "\n4️⃣ Moving Advanced Security Modules..."
echo "----------------------------------------"

if [ -d "agenticraft/security" ]; then
    # Move only advanced security features
    for file in agenticraft/security/*sandbox*.py agenticraft/security/*container*.py agenticraft/security/*isolation*.py; do
        if [ -f "$file" ]; then
            basename=$(basename "$file")
            safe_move "$file" "agenticraft/experimental/security/$basename"
        fi
    done
fi

echo -e "\n5️⃣ Moving Advanced Reasoning Modules..."
echo "----------------------------------------"

if [ -d "agenticraft/reasoning" ]; then
    # Move only advanced reasoning features
    for file in agenticraft/reasoning/*advanced*.py agenticraft/reasoning/*complex*.py agenticraft/reasoning/*chain*.py; do
        if [ -f "$file" ]; then
            basename=$(basename "$file")
            safe_move "$file" "agenticraft/experimental/reasoning/$basename"
        fi
    done
fi

echo -e "\n6️⃣ Updating Import Statements..."
echo "----------------------------------------"

# Update imports in all Python files
find agenticraft -name "*.py" -type f | while read file; do
    if grep -q "from agenticraft\.\(protocols\|mcp\|a2a\|fabric\|marketplace\)" "$file" 2>/dev/null; then
        update_imports "$file"
    fi
done

# Update test imports
find tests -name "*.py" -type f | while read file; do
    if grep -q "from agenticraft\.\(protocols\|mcp\|a2a\|fabric\|marketplace\)" "$file" 2>/dev/null; then
        update_imports "$file"
    fi
done

echo -e "\n7️⃣ Creating Compatibility Imports..."
echo "----------------------------------------"

# Create backwards compatibility in legacy module
cat > agenticraft/legacy/protocols.py << 'EOF'
"""Legacy protocol imports for backwards compatibility."""
import warnings

warnings.warn(
    "Importing protocols from agenticraft.legacy is deprecated. "
    "Use agenticraft.experimental.protocols instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location
from agenticraft.experimental.protocols import *
EOF

echo -e "\n8️⃣ Running Quick Validation..."
echo "----------------------------------------"

# Check that core imports still work
python -c "from agenticraft import Agent, Tool" 2>/dev/null && echo "✅ Core imports working" || echo "❌ Core imports broken!"

# Count files moved
experimental_count=$(find agenticraft/experimental -name "*.py" -type f | wc -l)
echo "✅ Moved $experimental_count files to experimental/"

echo -e "\n📊 Summary:"
echo "----------------------------------------"
echo "✅ Protocol modules moved to experimental/protocols/"
echo "✅ Fabric modules moved to experimental/fabric/"
echo "✅ Marketplace modules moved to experimental/marketplace/"
echo "✅ Advanced features moved to experimental/{security,reasoning}/"
echo "✅ Import statements updated"
echo "✅ Compatibility layer created"

echo -e "\n🧪 Next Step: Run tests to verify nothing broke"
echo "pytest tests/unit/core -v --tb=short"

echo -e "\n💡 If something broke:"
echo "1. Check the error message"
echo "2. Restore from backup: mv agenticraft_backup_week2/* agenticraft/"
echo "3. Fix the specific issue and try again"