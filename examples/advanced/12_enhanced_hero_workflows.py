"""Example: Using specialized agents with hero workflows.

This example demonstrates how to enhance the three hero workflows
with the new specialized agents added in Week 4.
"""

import asyncio
from typing import Dict, Any

from agenticraft.workflows import ResearchTeam, CustomerServiceDesk, CodeReviewPipeline
from agenticraft.agents.specialized import (
    SEOSpecialist,
    BusinessAnalyst,
    ProjectManager,
    DevOpsEngineer,
    QATester
)


async def enhanced_research_team_example():
    """Enhance Research Team with SEO optimization."""
    print("\n🔬 Enhanced Research Team with SEO Specialist\n")
    
    # Create research team
    team = ResearchTeam(size=5)
    
    # Create SEO specialist
    seo = SEOSpecialist(name="SEO Expert")
    
    # Conduct research
    topic = "Best practices for multi-agent AI systems"
    print(f"Researching: {topic}")
    
    report = await team.research(topic)
    
    # Optimize the report for SEO
    print("\n🔍 Optimizing report for search engines...")
    
    # Extract executive summary for SEO analysis
    content = report.get("executive_summary", "")
    
    # Get keyword suggestions
    keywords = await seo.suggest_keywords(topic, intent="informational")
    print(f"\nSuggested keywords: {keywords['primary_keywords'][:3]}")
    
    # Analyze content for SEO
    seo_analysis = await seo.analyze_content(
        content,
        target_keywords=keywords['primary_keywords'][:3]
    )
    
    print(f"SEO Score: {seo_analysis['seo_score']}/100")
    print("\nSEO Recommendations:")
    for rec in seo_analysis['recommendations'][:3]:
        print(f"- {rec}")
    
    # Optimize meta tags
    meta = await seo.optimize_meta_tags(
        title=f"Research Report: {topic}",
        description=content[:150],
        keywords=keywords['primary_keywords']
    )
    
    print(f"\nOptimized Title: {meta['optimized']['title']}")
    
    return {
        "report": report,
        "seo_optimization": seo_analysis,
        "keywords": keywords,
        "meta_tags": meta
    }


async def enhanced_customer_service_example():
    """Enhance Customer Service with Business Analysis."""
    print("\n💬 Enhanced Customer Service with Business Analyst\n")
    
    # Create customer service desk
    desk = CustomerServiceDesk(tiers=["L1", "L2", "Expert"])
    
    # Create business analyst
    ba = BusinessAnalyst(name="Process Optimizer")
    
    # Simulate customer inquiries
    inquiries = [
        {"id": 1, "type": "billing", "complexity": "simple"},
        {"id": 2, "type": "technical", "complexity": "complex"},
        {"id": 3, "type": "feature_request", "complexity": "medium"}
    ]
    
    print("Processing customer inquiries...")
    responses = []
    for inquiry in inquiries:
        response = await desk.handle(inquiry)
        responses.append(response)
        print(f"- Inquiry {inquiry['id']}: Handled by {response.get('tier', 'L1')}")
    
    # Analyze the customer service process
    print("\n📊 Analyzing customer service process...")
    
    current_process = {
        "steps": [
            {"id": 1, "name": "Inquiry Receipt", "duration": "2 min", "actors": ["Customer"]},
            {"id": 2, "name": "L1 Review", "duration": "10 min", "actors": ["L1 Agent"]},
            {"id": 3, "name": "Escalation Decision", "duration": "5 min", "actors": ["L1 Agent"]},
            {"id": 4, "name": "L2 Handling", "duration": "30 min", "actors": ["L2 Agent"]},
            {"id": 5, "name": "Resolution", "duration": "5 min", "actors": ["Agent"]}
        ]
    }
    
    process_analysis = await ba.create_process_map(
        "Customer Service Workflow",
        current_state=current_process
    )
    
    print(f"\nCurrent process duration: {process_analysis['current_process']['total_duration']}")
    print(f"Optimized process duration: {process_analysis['optimized_process']['total_duration']}")
    print(f"Efficiency gain: {process_analysis['metrics']['efficiency_gain']}")
    
    print("\nProcess improvements:")
    for improvement in process_analysis['optimized_process']['improvements']:
        print(f"- {improvement}")
    
    # Create business case for improvements
    business_case = await ba.create_business_case(
        "Customer Service Optimization",
        investment=50000,
        benefits=[
            "Reduce average handling time by 30%",
            "Increase customer satisfaction by 20%",
            "Enable 24/7 automated support"
        ]
    )
    
    print(f"\nBusiness Case:")
    print(f"- ROI: {business_case['financial_analysis']['roi']}")
    print(f"- Payback Period: {business_case['financial_analysis']['payback_period']}")
    print(f"- Recommendation: {business_case['recommendation']}")
    
    return {
        "service_metrics": responses,
        "process_analysis": process_analysis,
        "business_case": business_case
    }


async def enhanced_code_review_example():
    """Enhance Code Review with comprehensive testing and deployment."""
    print("\n👨‍💻 Enhanced Code Review Pipeline with QA and DevOps\n")
    
    # Create code review pipeline
    pipeline = CodeReviewPipeline()
    
    # Create additional agents
    qa = QATester(name="QA Specialist")
    devops = DevOpsEngineer(name="DevOps Expert")
    pm = ProjectManager(name="Tech Lead")
    
    # Sample code for review
    code_sample = """
def calculate_discount(price: float, customer_type: str) -> float:
    if customer_type == "premium":
        return price * 0.8
    elif customer_type == "regular":
        return price * 0.95
    return price
    
def process_order(items: list, customer_type: str) -> dict:
    total = sum(item['price'] for item in items)
    discount = calculate_discount(total, customer_type)
    return {
        'subtotal': total,
        'discount': total - discount,
        'total': discount
    }
"""
    
    # 1. Code Review
    print("1️⃣ Performing code review...")
    review_result = await pipeline.review({
        "code": code_sample,
        "language": "python",
        "pr_title": "Add discount calculation feature"
    })
    
    print(f"Security Score: {review_result['security_score']}/10")
    print(f"Quality Score: {review_result['quality_score']}/10")
    
    # 2. Generate Test Cases
    print("\n2️⃣ Generating test cases...")
    test_cases = await qa.generate_test_cases(
        "Discount calculation and order processing",
        test_type="unit"
    )
    
    print(f"Generated {test_cases['test_summary']['total']} test cases:")
    print(f"- Positive: {test_cases['test_summary']['by_category']['positive']}")
    print(f"- Negative: {test_cases['test_summary']['by_category']['negative']}")
    print(f"- Edge cases: {test_cases['test_summary']['by_category']['edge']}")
    
    # 3. Create Deployment Plan
    print("\n3️⃣ Creating deployment plan...")
    deployment_plan = await devops.plan_deployment(
        service="order-service",
        version="1.2.0",
        environment="production",
        strategy="canary"
    )
    
    print(f"Deployment strategy: {deployment_plan['plan']['strategy']}")
    print(f"Estimated time: {deployment_plan['plan']['estimated_time']}")
    print("\nDeployment steps:")
    for step in deployment_plan['plan']['steps'][:3]:
        print(f"- {step}")
    
    # 4. Performance Test Design
    print("\n4️⃣ Designing performance tests...")
    perf_test = await qa.perform_performance_test(
        endpoint="/api/orders/calculate-discount",
        load_profile={
            "users": 1000,
            "ramp_up": 60,
            "duration": 300
        }
    )
    
    print("Performance test scenarios:")
    for scenario in perf_test['test_scenarios']:
        print(f"- {scenario['name']}: {scenario['users']} users")
    
    # 5. Create monitoring setup
    print("\n5️⃣ Setting up monitoring...")
    monitoring = await devops.setup_monitoring(
        service="order-service",
        metrics=["response_time", "error_rate", "throughput"]
    )
    
    print(f"Configured {len(monitoring['alerts'])} alerts")
    print("Monitoring dashboards created")
    
    # 6. Project tracking
    print("\n6️⃣ Creating project plan...")
    tasks = [
        {"id": 1, "title": "Code Review", "estimated_hours": 2, "status": "completed"},
        {"id": 2, "title": "Write Tests", "estimated_hours": 4, "status": "in_progress"},
        {"id": 3, "title": "Performance Testing", "estimated_hours": 3, "status": "todo"},
        {"id": 4, "title": "Deployment", "estimated_hours": 2, "status": "todo"},
        {"id": 5, "title": "Monitoring Setup", "estimated_hours": 2, "status": "todo"}
    ]
    
    progress = await pm.track_progress({
        "tasks": tasks,
        "days_elapsed": 2,
        "deadline": "2024-04-15"
    })
    
    print(f"\nProject Progress: {progress['summary']['completion_percentage']}%")
    print(f"Velocity: {progress['velocity']['current']} tasks/day")
    print(f"Estimated completion: {progress['timeline']['estimated_completion']}")
    
    return {
        "code_review": review_result,
        "test_cases": test_cases,
        "deployment_plan": deployment_plan,
        "performance_tests": perf_test,
        "monitoring": monitoring,
        "project_status": progress
    }


async def main():
    """Run all enhanced workflow examples."""
    print("=" * 60)
    print("AgentiCraft: Enhanced Hero Workflows with Specialized Agents")
    print("=" * 60)
    
    # Run enhanced research team
    research_result = await enhanced_research_team_example()
    
    print("\n" + "-" * 60)
    
    # Run enhanced customer service
    service_result = await enhanced_customer_service_example()
    
    print("\n" + "-" * 60)
    
    # Run enhanced code review
    review_result = await enhanced_code_review_example()
    
    print("\n" + "=" * 60)
    print("✅ All enhanced workflows completed successfully!")
    print("\nKey Insights:")
    print("- Research Team + SEO = Content optimized for discovery")
    print("- Customer Service + BA = Process optimization & ROI")
    print("- Code Review + QA/DevOps = Production-ready deployment")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
