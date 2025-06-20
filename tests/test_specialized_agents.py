#!/usr/bin/env python3
"""Quick test script to verify all specialized agents are working."""

import asyncio
import sys
from typing import List, Tuple

# Add the project root to the path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agenticraft.agents.specialized import (
    WebResearcher,
    DataAnalyst,
    TechnicalWriter,
    CodeReviewer,
    SEOSpecialist,
    DevOpsEngineer,
    ProjectManager,
    BusinessAnalyst,
    QATester
)


async def test_agent(agent_class, method_name: str, args: dict) -> Tuple[str, bool, str]:
    """Test a single agent method."""
    agent_name = agent_class.__name__
    try:
        agent = agent_class()
        method = getattr(agent, method_name)
        result = await method(**args)
        
        # Check if result has expected structure
        if isinstance(result, dict) and "reasoning" in result:
            return agent_name, True, "✅ Success with reasoning"
        elif isinstance(result, dict):
            return agent_name, True, "✅ Success"
        else:
            return agent_name, False, "❌ Unexpected result format"
    except Exception as e:
        return agent_name, False, f"❌ Error: {str(e)[:50]}..."


async def run_all_tests():
    """Run tests for all specialized agents."""
    print("=" * 60)
    print("Testing All Specialized Agents")
    print("=" * 60)
    
    # Define test cases
    test_cases = [
        # Original agents
        (WebResearcher, "research", {"topic": "test topic"}),
        (DataAnalyst, "analyze", {"data": [1, 2, 3, 4, 5]}),
        (TechnicalWriter, "write", {"topic": "test documentation", "style": "technical"}),
        (CodeReviewer, "review_code", {"code": "def test(): pass", "language": "python"}),
        
        # New agents
        (SEOSpecialist, "suggest_keywords", {"topic": "AI technology", "intent": "informational"}),
        (DevOpsEngineer, "plan_deployment", {
            "service": "test-service",
            "version": "1.0.0",
            "environment": "staging",
            "strategy": "rolling"
        }),
        (ProjectManager, "create_project_plan", {
            "project_name": "Test Project",
            "requirements": ["Feature A", "Feature B"],
            "team_size": 5
        }),
        (BusinessAnalyst, "analyze_requirements", {
            "project_description": "New e-commerce platform",
            "stakeholders": ["Sales", "IT"]
        }),
        (QATester, "create_test_plan", {
            "project_name": "Test Project",
            "features": ["Login", "Dashboard"],
            "test_types": ["unit", "functional"]
        })
    ]
    
    # Run all tests
    results = await asyncio.gather(
        *[test_agent(agent_class, method, args) 
          for agent_class, method, args in test_cases]
    )
    
    # Display results
    print("\nTest Results:")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for agent_name, success, message in results:
        status = "PASS" if success else "FAIL"
        print(f"{agent_name:20} | {status:4} | {message}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"\nSummary: {passed} passed, {failed} failed out of {len(results)} tests")
    
    # Test agent count
    expected_agents = 9
    actual_agents = len(test_cases)
    print(f"\nAgent Count: {actual_agents}/{expected_agents} agents tested")
    
    if passed == len(results):
        print("\n✅ All tests passed! All specialized agents are working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please check the errors above.")
    
    return passed == len(results)


async def test_reasoning_transparency():
    """Test that agents provide reasoning transparency."""
    print("\n" + "=" * 60)
    print("Testing Reasoning Transparency")
    print("=" * 60)
    
    # Test SEO Specialist reasoning
    seo = SEOSpecialist()
    result = await seo.analyze_content(
        "This is a test article about artificial intelligence and machine learning.",
        ["AI", "machine learning"]
    )
    
    print("\nSEO Specialist Reasoning:")
    if hasattr(seo, 'last_reasoning') and seo.last_reasoning:
        print(f"- Initial: {seo.last_reasoning.initial_thought}")
        print(f"- Thoughts: {len(seo.last_reasoning.thoughts)} steps")
        print(f"- Decision: {seo.last_reasoning.final_decision}")
    else:
        print("❌ No reasoning found")
    
    # Test Project Manager reasoning
    pm = ProjectManager()
    plan = await pm.prioritize_tasks([
        {"title": "Critical bug fix", "priority": "high"},
        {"title": "New feature", "priority": "medium"},
        {"title": "Documentation update", "priority": "low"}
    ])
    
    print("\nProject Manager Reasoning:")
    if hasattr(pm, 'last_reasoning') and pm.last_reasoning:
        print(f"- Initial: {pm.last_reasoning.initial_thought}")
        print(f"- Decision: {pm.last_reasoning.final_decision}")
    else:
        print("❌ No reasoning found")
    
    print("\n✅ Reasoning transparency test complete")


async def main():
    """Run all test suites."""
    # Run basic functionality tests
    all_passed = await run_all_tests()
    
    # Run reasoning transparency tests
    await test_reasoning_transparency()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All specialized agents are ready for use!")
    else:
        print("⚠️  Some issues found. Please review the test results.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
