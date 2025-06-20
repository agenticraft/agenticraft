#!/bin/bash
# Quick fix for hanging tests

echo "🛑 Stopping hanging tests..."
pkill -f pytest 2>/dev/null
pkill -f run_full_tests 2>/dev/null

echo "✅ Processes stopped"
echo ""
echo "🚀 Running ONLY fast, reliable tests..."

# Run a minimal test set first
pytest tests/unit/core/test_*.py \
    -v \
    --timeout=10 \
    --timeout-method=thread \
    -x \
    --tb=short \
    > quick_test_results.txt 2>&1

echo "📊 Quick test results:"
tail -20 quick_test_results.txt

# Now try to get coverage on core modules only
echo -e "\n📈 Getting coverage for core modules..."
pytest tests/unit/core/ \
    --cov=agenticraft.core \
    --cov-report=term \
    --timeout=10 \
    -q \
    > core_coverage.txt 2>&1

echo -e "\n📊 Core coverage:"
grep -A10 "TOTAL" core_coverage.txt || tail -10 core_coverage.txt

echo -e "\n✅ Quick test run complete!"
echo -e "\n💡 Next steps:"
echo "1. Check which test directories have issues:"
echo "   for dir in tests/*/; do echo -n \"\$dir: \"; timeout 5s pytest \"\$dir\" -q 2>&1 | grep -E '(passed|failed|ERROR)' | head -1; done"
echo ""
echo "2. Run only working tests:"
echo "   pytest tests/unit -k 'not (websocket or integration or security)' --timeout=30"
echo ""
echo "3. Skip all problematic tests for now:"
echo "   pytest -v --timeout=30 -k 'not (websocket or server or integration or async or thread)'"