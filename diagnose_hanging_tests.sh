#!/bin/bash
# Diagnose which tests are hanging

echo "🔍 Diagnosing Hanging Tests"
echo "=========================="

# Kill any existing pytest processes
echo -e "\n🛑 Stopping any running pytest processes..."
pkill -f pytest 2>/dev/null
sleep 2

# Run tests with timeout and verbose output to see where it hangs
echo -e "\n🧪 Running tests with timeout and verbose output..."
echo "This will show which test is hanging..."

# First, try running just unit tests (usually faster)
echo -e "\n1️⃣ Testing unit tests only (30s timeout per test)..."
pytest tests/unit/ \
    -v \
    --timeout=30 \
    --timeout-method=thread \
    -x \
    --tb=short \
    2>&1 | tee unit_test_output.txt &

# Give it 60 seconds total
sleep 60

# If still running, kill it
if pgrep -f pytest > /dev/null; then
    echo -e "\n⚠️  Unit tests hanging, killing process..."
    pkill -f pytest
    echo "Last 20 lines before hang:"
    tail -20 unit_test_output.txt
fi

# Now try to identify specific problematic test files
echo -e "\n2️⃣ Finding problematic test files..."

# List of test directories to check
test_dirs=(
    "tests/unit"
    "tests/integration" 
    "tests/examples"
    "tests/fabric"
    "tests/protocols"
    "tests/security"
    "tests/reasoning"
    "tests/marketplace"
    "tests/telemetry"
    "tests/workflows"
    "tests/memory"
)

# Test each directory with a short timeout
for dir in "${test_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "\n📁 Testing $dir..."
        timeout 10s pytest "$dir" -v --tb=no -q 2>&1 | head -5
        if [ $? -eq 124 ]; then
            echo "   ⚠️  TIMEOUT - This directory has hanging tests!"
        else
            echo "   ✅ OK"
        fi
    fi
done

# Check for specific patterns that cause hangs
echo -e "\n3️⃣ Checking for common hang patterns..."

# Look for infinite loops
echo -e "\n🔍 Checking for while True loops..."
grep -r "while True:" tests/ --include="*.py" | grep -v "break" | head -10

# Look for blocking I/O
echo -e "\n🔍 Checking for blocking I/O operations..."
grep -r -E "(input\(|socket\.|server\.|listen\(|accept\()" tests/ --include="*.py" | head -10

# Look for threading issues
echo -e "\n🔍 Checking for threading without timeouts..."
grep -r -E "(Thread\(|threading\.|asyncio\.run)" tests/ --include="*.py" | head -10

# Create a safe test runner
echo -e "\n4️⃣ Creating safe test runner..."
cat > run_safe_tests.py << 'EOF'
import subprocess
import sys
import time

def run_tests_with_timeout(test_path, timeout=300):
    """Run tests with a timeout"""
    print(f"\n🧪 Running tests in {test_path} (timeout: {timeout}s)...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short", 
             "--timeout=30", "--timeout-method=thread", "-x"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠️  TIMEOUT: Tests in {test_path} took longer than {timeout}s")
        return False

# Test each major test group
test_groups = [
    ("tests/unit", 60),
    ("tests/examples", 60),
    ("tests/fabric", 60),
    ("tests/integration", 120),
    ("tests -k 'not (integration or security or websocket)'", 180),
]

for test_path, timeout in test_groups:
    success = run_tests_with_timeout(test_path, timeout)
    if not success:
        print(f"❌ Issues found in {test_path}")
    else:
        print(f"✅ {test_path} completed successfully")
EOF

echo -e "\n✅ Diagnostic complete!"
echo -e "\n📋 Recommendations:"
echo "1. Check unit_test_output.txt to see where tests hang"
echo "2. Look for test directories marked with TIMEOUT"
echo "3. Exclude problematic tests with -k 'not testname'"
echo "4. Run: python run_safe_tests.py for a safer test execution"
echo -e "\n💡 Quick fix - run only fast tests:"
echo "pytest tests/unit -v --timeout=30 -x"