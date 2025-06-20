#!/bin/bash
# Analyze which modules should be moved to experimental

echo "🔍 Analyzing Modules for Week 2 Reorganization"
echo "=============================================="

# Function to count files in a directory
count_files() {
    find "$1" -name "*.py" -type f 2>/dev/null | wc -l | tr -d ' '
}

# Function to check test failures
check_test_failures() {
    grep -l "$1" test_full_report.txt 2>/dev/null | wc -l | tr -d ' '
}

echo -e "\n📊 Current Module Analysis:"
echo -e "\n1️⃣ Protocol-related modules:"
echo "----------------------------------------"
for pattern in "protocol" "mcp" "a2a" "acp" "anp"; do
    files=$(find agenticraft -name "*${pattern}*.py" -type f 2>/dev/null | grep -v __pycache__ | grep -v experimental)
    count=$(echo "$files" | grep -c "^" 2>/dev/null || echo "0")
    if [ "$count" -gt 0 ]; then
        echo -e "\n${pattern^^} modules ($count files):"
        echo "$files" | head -5
        [ "$count" -gt 5 ] && echo "... and $((count-5)) more"
    fi
done

echo -e "\n2️⃣ Fabric modules:"
echo "----------------------------------------"
if [ -d "agenticraft/fabric" ]; then
    count=$(count_files "agenticraft/fabric")
    echo "Fabric directory: $count files"
    ls agenticraft/fabric/*.py 2>/dev/null | head -5
fi

echo -e "\n3️⃣ Marketplace modules:"
echo "----------------------------------------"
files=$(find agenticraft -name "*marketplace*.py" -type f 2>/dev/null | grep -v __pycache__)
count=$(echo "$files" | grep -c "^" 2>/dev/null || echo "0")
if [ "$count" -gt 0 ]; then
    echo "Marketplace modules: $count files"
    echo "$files"
fi

echo -e "\n4️⃣ Advanced Security modules:"
echo "----------------------------------------"
if [ -d "agenticraft/security" ]; then
    echo "Security modules to evaluate:"
    ls agenticraft/security/*.py 2>/dev/null | while read file; do
        basename=$(basename "$file")
        case "$basename" in
            *sandbox* | *container* | *isolation*)
                echo "  → $basename (MOVE to experimental)"
                ;;
            *)
                echo "  ✓ $basename (KEEP in core)"
                ;;
        esac
    done
fi

echo -e "\n5️⃣ Advanced Reasoning modules:"
echo "----------------------------------------"
if [ -d "agenticraft/reasoning" ]; then
    echo "Reasoning modules to evaluate:"
    ls agenticraft/reasoning/*.py 2>/dev/null | while read file; do
        basename=$(basename "$file")
        case "$basename" in
            *advanced* | *complex* | *chain*)
                echo "  → $basename (MOVE to experimental)"
                ;;
            *)
                echo "  ✓ $basename (KEEP in core)"
                ;;
        esac
    done
fi

echo -e "\n6️⃣ Test Failure Analysis:"
echo "----------------------------------------"
if [ -f "test_full_report.txt" ]; then
    echo "Modules mentioned in failing tests:"
    grep -E "FAILED tests.*::" test_full_report.txt | grep -oE "test_[a-z_]+\.py" | sort | uniq -c | sort -rn | head -10
fi

echo -e "\n7️⃣ Utility Modules to Consolidate:"
echo "----------------------------------------"
echo "Config-related files:"
find agenticraft -name "*config*.py" -type f | grep -v __pycache__ | grep -v test | wc -l
echo "Logging-related files:"
find agenticraft -name "*log*.py" -type f | grep -v __pycache__ | grep -v test | wc -l
echo "Helper/Util files:"
find agenticraft -name "*util*.py" -o -name "*helper*.py" -type f | grep -v __pycache__ | grep -v test | wc -l

echo -e "\n📋 Summary Recommendations:"
echo "----------------------------------------"
echo "→ MOVE to experimental/protocols: All MCP, A2A, ACP, ANP files"
echo "→ MOVE to experimental/fabric: Entire fabric directory"
echo "→ MOVE to experimental/marketplace: All marketplace files"
echo "→ MOVE to experimental/security: Advanced sandbox implementations"
echo "→ MOVE to experimental/reasoning: Advanced reasoning chains"
echo "→ CONSOLIDATE in utils/: All config, logging, helper files"

echo -e "\n💾 Creating detailed module inventory..."
cat > modules_to_move.txt << 'EOF'
# Modules to Move to Experimental

## Protocols (Priority 1)
EOF

find agenticraft -name "*mcp*.py" -o -name "*a2a*.py" -o -name "*protocol*.py" | grep -v __pycache__ | grep -v test | sort >> modules_to_move.txt

cat >> modules_to_move.txt << 'EOF'

## Fabric (Priority 2)
EOF

find agenticraft/fabric -name "*.py" | grep -v __pycache__ | sort >> modules_to_move.txt 2>/dev/null

cat >> modules_to_move.txt << 'EOF'

## Marketplace (Priority 3)
EOF

find agenticraft -name "*marketplace*.py" | grep -v __pycache__ | sort >> modules_to_move.txt

echo -e "\n✅ Analysis complete! Check modules_to_move.txt for full list"
echo -e "\n🚀 Ready to start moving? Run: ./move_experimental_modules.sh"