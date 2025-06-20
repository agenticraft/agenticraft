"""QA Tester Agent - Created for AgentiCraft.

A specialized agent for quality assurance, test planning, and bug tracking.
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from agenticraft.core.agent import Agent, AgentConfig
from agenticraft.core.reasoning import ReasoningTrace, SimpleReasoning


class TestType(Enum):
    """Types of testing"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    REGRESSION = "regression"
    ACCEPTANCE = "acceptance"


class BugSeverity(Enum):
    """Bug severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class QATester(Agent):
    """
    QA tester agent for comprehensive testing and quality assurance.
    
    Focuses on:
    - Test plan creation and execution
    - Test case design and automation
    - Bug identification and tracking
    - Performance and security testing
    - Quality metrics and reporting
    """
    
    def __init__(self, name: str = "QA Tester", **kwargs):
        config = AgentConfig(
            name=name,
            role="qa_tester",
            specialty="quality assurance and testing",
            personality_traits={
                "detail_oriented": 0.9,
                "systematic": 0.9,
                "critical_thinking": 0.8,
                "patient": 0.7,
                "curious": 0.8
            },
            **kwargs
        )
        super().__init__(config)
        
        # Testing knowledge base
        self.test_patterns = {
            "boundary": "Test edge cases and limits",
            "negative": "Test invalid inputs and error conditions",
            "positive": "Test normal expected behavior",
            "stress": "Test under high load conditions"
        }
    
    async def create_test_plan(self,
                              project_name: str,
                              features: List[str],
                              test_types: List[str] = None) -> Dict[str, Any]:
        """Create comprehensive test plan for project."""
        thought = SimpleReasoning(
            initial_thought=f"Creating test plan for {project_name} with {len(features)} features"
        )
        
        if not test_types:
            test_types = ["unit", "integration", "functional", "acceptance"]
        
        thought.add_thought(f"Planning for test types: {', '.join(test_types)}")
        
        # Create test strategy
        test_strategy = {
            "approach": "Risk-based testing with automation where applicable",
            "scope": features,
            "test_types": test_types,
            "environments": ["Development", "Staging", "Production-like"],
            "tools": self._recommend_test_tools(test_types)
        }
        
        # Generate test scenarios for each feature
        test_scenarios = []
        total_test_cases = 0
        
        for feature in features:
            scenarios = self._generate_test_scenarios(feature, test_types)
            test_scenarios.extend(scenarios)
            total_test_cases += sum(s["estimated_test_cases"] for s in scenarios)
        
        thought.add_thought(f"Generated {len(test_scenarios)} test scenarios with ~{total_test_cases} test cases")
        
        # Create test schedule
        test_schedule = self._create_test_schedule(test_scenarios, test_types)
        
        # Define test metrics
        test_metrics = {
            "test_coverage": "Percentage of requirements covered by tests",
            "defect_density": "Defects per 1000 lines of code",
            "test_execution_rate": "Test cases executed per day",
            "defect_detection_rate": "Defects found per test cycle",
            "automation_percentage": "Percentage of automated test cases"
        }
        
        # Risk assessment
        risks = [
            {
                "risk": "Insufficient test data",
                "impact": "Incomplete test coverage",
                "mitigation": "Create comprehensive test data sets"
            },
            {
                "risk": "Limited testing time",
                "impact": "Reduced test coverage",
                "mitigation": "Prioritize critical paths and automate repetitive tests"
            }
        ]
        
        thought.set_final_decision(
            f"Test plan created with {len(test_scenarios)} scenarios covering {len(features)} features"
        )
        self.last_reasoning = thought
        
        return {
            "project_name": project_name,
            "test_strategy": test_strategy,
            "test_scenarios": test_scenarios,
            "test_schedule": test_schedule,
            "estimated_effort": {
                "total_test_cases": total_test_cases,
                "manual_effort_hours": total_test_cases * 0.5,  # 30 min per test case
                "automation_effort_hours": total_test_cases * 0.2  # 12 min per automated test
            },
            "test_metrics": test_metrics,
            "risks": risks,
            "entry_criteria": [
                "Code complete for feature",
                "Unit tests passing",
                "Test environment available",
                "Test data prepared"
            ],
            "exit_criteria": [
                "All critical test cases executed",
                "No critical defects open",
                "Test coverage > 80%",
                "Performance benchmarks met"
            ],
            "reasoning": thought.to_dict()
        }
    
    async def generate_test_cases(self,
                                feature_description: str,
                                test_type: str = "functional") -> Dict[str, Any]:
        """Generate detailed test cases for a feature."""
        thought = SimpleReasoning(
            initial_thought=f"Generating {test_type} test cases for: {feature_description[:50]}..."
        )
        
        test_cases = []
        test_case_id = 1
        
        # Positive test cases
        thought.add_thought("Creating positive test cases")
        positive_cases = self._generate_positive_tests(feature_description, test_type)
        for case in positive_cases:
            test_cases.append({
                "id": f"TC{test_case_id:03d}",
                "type": test_type,
                "category": "positive",
                "title": case["title"],
                "description": case["description"],
                "preconditions": case.get("preconditions", ["System is accessible"]),
                "steps": case["steps"],
                "expected_result": case["expected"],
                "priority": "high",
                "automated": case.get("automated", False)
            })
            test_case_id += 1
        
        # Negative test cases
        thought.add_thought("Creating negative test cases")
        negative_cases = self._generate_negative_tests(feature_description, test_type)
        for case in negative_cases:
            test_cases.append({
                "id": f"TC{test_case_id:03d}",
                "type": test_type,
                "category": "negative",
                "title": case["title"],
                "description": case["description"],
                "preconditions": case.get("preconditions", ["System is accessible"]),
                "steps": case["steps"],
                "expected_result": case["expected"],
                "priority": "medium",
                "automated": case.get("automated", False)
            })
            test_case_id += 1
        
        # Edge cases
        thought.add_thought("Creating edge case tests")
        edge_cases = self._generate_edge_cases(feature_description, test_type)
        for case in edge_cases:
            test_cases.append({
                "id": f"TC{test_case_id:03d}",
                "type": test_type,
                "category": "edge",
                "title": case["title"],
                "description": case["description"],
                "preconditions": case.get("preconditions", ["System is accessible"]),
                "steps": case["steps"],
                "expected_result": case["expected"],
                "priority": "medium",
                "automated": case.get("automated", False)
            })
            test_case_id += 1
        
        # Generate test data requirements
        test_data = self._identify_test_data_needs(test_cases)
        
        # Automation recommendations
        automation_candidates = [tc for tc in test_cases if self._is_automation_candidate(tc)]
        
        thought.set_final_decision(
            f"Generated {len(test_cases)} test cases: "
            f"{len(positive_cases)} positive, {len(negative_cases)} negative, {len(edge_cases)} edge cases"
        )
        self.last_reasoning = thought
        
        return {
            "feature": feature_description,
            "test_cases": test_cases,
            "test_summary": {
                "total": len(test_cases),
                "by_category": {
                    "positive": len(positive_cases),
                    "negative": len(negative_cases),
                    "edge": len(edge_cases)
                },
                "automation_candidates": len(automation_candidates)
            },
            "test_data_requirements": test_data,
            "automation_recommendations": [
                f"Automate {tc['id']}: {tc['title']}" 
                for tc in automation_candidates[:5]
            ],
            "coverage_assessment": self._assess_test_coverage(test_cases, feature_description),
            "reasoning": thought.to_dict()
        }
    
    async def report_bug(self,
                        title: str,
                        description: str,
                        steps_to_reproduce: List[str],
                        expected_behavior: str,
                        actual_behavior: str,
                        test_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Create detailed bug report."""
        thought = SimpleReasoning(
            initial_thought=f"Creating bug report: {title}"
        )
        
        # Analyze bug severity
        severity = self._assess_bug_severity(description, actual_behavior)
        thought.add_thought(f"Assessed severity as: {severity}")
        
        # Determine bug category
        category = self._categorize_bug(description, actual_behavior)
        
        # Generate bug ID
        bug_id = f"BUG-{len(title)}{len(description)}"[:10]
        
        # Create detailed bug report
        bug_report = {
            "id": bug_id,
            "title": title,
            "description": description,
            "severity": severity,
            "priority": self._determine_priority(severity, category),
            "category": category,
            "status": "open",
            "reporter": self.config.name,
            "steps_to_reproduce": steps_to_reproduce,
            "expected_behavior": expected_behavior,
            "actual_behavior": actual_behavior,
            "test_data": test_data or {},
            "environment": {
                "browser": "Chrome 120",
                "os": "Windows 10",
                "test_environment": "Staging"
            },
            "attachments": ["screenshot.png", "console_log.txt"],
            "impact_analysis": self._analyze_bug_impact(severity, category),
            "suggested_fix": self._suggest_fix_approach(description, category),
            "related_test_cases": self._find_related_test_cases(title, category)
        }
        
        # Root cause analysis
        thought.add_thought("Performing root cause analysis")
        root_cause = self._analyze_root_cause(description, actual_behavior, category)
        bug_report["root_cause_analysis"] = root_cause
        
        # Regression risk
        regression_risk = self._assess_regression_risk(category, severity)
        bug_report["regression_risk"] = regression_risk
        
        thought.set_final_decision(f"Bug report created: {severity} severity, {category} category")
        self.last_reasoning = thought
        
        return {
            "bug_report": bug_report,
            "recommendations": [
                "Assign to development team immediately" if severity in ["critical", "high"] else "Include in next sprint",
                "Add automated test to prevent regression" if regression_risk == "high" else "Update existing test cases",
                "Review similar functionality for related issues"
            ],
            "test_implications": {
                "additional_tests_needed": self._identify_additional_tests(category),
                "regression_suite_update": regression_risk == "high"
            },
            "reasoning": thought.to_dict()
        }
    
    async def perform_performance_test(self,
                                     endpoint: str,
                                     load_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """Design and analyze performance test."""
        thought = SimpleReasoning(
            initial_thought=f"Designing performance test for endpoint: {endpoint}"
        )
        
        if not load_profile:
            load_profile = {
                "users": 100,
                "ramp_up": 60,  # seconds
                "duration": 300,  # seconds
                "think_time": 5  # seconds
            }
        
        thought.add_thought(f"Load profile: {load_profile['users']} users over {load_profile['duration']}s")
        
        # Create test scenarios
        test_scenarios = [
            {
                "name": "Normal Load",
                "users": load_profile["users"],
                "duration": load_profile["duration"],
                "expected_response_time": 500,  # ms
                "expected_throughput": 200  # requests/sec
            },
            {
                "name": "Peak Load",
                "users": load_profile["users"] * 2,
                "duration": load_profile["duration"] // 2,
                "expected_response_time": 1000,  # ms
                "expected_throughput": 150  # requests/sec
            },
            {
                "name": "Stress Test",
                "users": load_profile["users"] * 5,
                "duration": 60,
                "expected_response_time": 2000,  # ms
                "expected_throughput": 100  # requests/sec
            }
        ]
        
        # Simulate test results
        test_results = []
        for scenario in test_scenarios:
            result = {
                "scenario": scenario["name"],
                "metrics": {
                    "avg_response_time": scenario["expected_response_time"] * (0.8 + 0.4 * len(endpoint) / 20),
                    "p95_response_time": scenario["expected_response_time"] * 1.5,
                    "p99_response_time": scenario["expected_response_time"] * 2,
                    "throughput": scenario["expected_throughput"] * (0.7 + 0.3 * len(endpoint) / 20),
                    "error_rate": 0.1 if scenario["name"] == "Normal Load" else 0.5 if scenario["name"] == "Peak Load" else 2.0,
                    "cpu_usage": 40 if scenario["name"] == "Normal Load" else 70 if scenario["name"] == "Peak Load" else 95,
                    "memory_usage": 60 if scenario["name"] == "Normal Load" else 75 if scenario["name"] == "Peak Load" else 85
                },
                "passed": scenario["name"] != "Stress Test"
            }
            test_results.append(result)
        
        # Analyze results
        performance_issues = []
        for result in test_results:
            if result["metrics"]["avg_response_time"] > result["scenario"]["expected_response_time"]:
                performance_issues.append({
                    "issue": "Response time exceeds threshold",
                    "scenario": result["scenario"],
                    "severity": "high" if result["scenario"] == "Normal Load" else "medium"
                })
            
            if result["metrics"]["error_rate"] > 1.0:
                performance_issues.append({
                    "issue": "High error rate",
                    "scenario": result["scenario"],
                    "severity": "critical" if result["scenario"] != "Stress Test" else "medium"
                })
        
        thought.add_thought(f"Identified {len(performance_issues)} performance issues")
        
        # Generate recommendations
        recommendations = self._generate_performance_recommendations(test_results, performance_issues)
        
        thought.set_final_decision(
            f"Performance test complete: {len(test_scenarios)} scenarios tested, "
            f"{len(performance_issues)} issues found"
        )
        self.last_reasoning = thought
        
        return {
            "endpoint": endpoint,
            "load_profile": load_profile,
            "test_scenarios": test_scenarios,
            "test_results": test_results,
            "performance_issues": performance_issues,
            "recommendations": recommendations,
            "performance_baseline": {
                "acceptable_response_time": 500,
                "acceptable_throughput": 200,
                "max_error_rate": 0.5
            },
            "optimization_suggestions": [
                "Implement caching for frequently accessed data",
                "Optimize database queries",
                "Consider horizontal scaling for high load",
                "Review and optimize API payload size"
            ],
            "reasoning": thought.to_dict()
        }
    
    def _recommend_test_tools(self, test_types: List[str]) -> Dict[str, str]:
        """Recommend testing tools based on test types."""
        tool_map = {
            "unit": "Jest, pytest, JUnit",
            "integration": "Postman, REST Assured, Supertest",
            "functional": "Selenium, Cypress, Playwright",
            "performance": "JMeter, K6, Gatling",
            "security": "OWASP ZAP, Burp Suite",
            "usability": "UserTesting, Maze",
            "regression": "TestComplete, Katalon",
            "acceptance": "Cucumber, SpecFlow"
        }
        
        return {test_type: tool_map.get(test_type, "Manual testing") for test_type in test_types}
    
    def _generate_test_scenarios(self, feature: str, test_types: List[str]) -> List[Dict]:
        """Generate test scenarios for a feature."""
        scenarios = []
        
        for test_type in test_types:
            if test_type == "functional":
                scenarios.append({
                    "feature": feature,
                    "scenario": f"Verify {feature} works as expected",
                    "test_type": test_type,
                    "estimated_test_cases": 10,
                    "priority": "high",
                    "automation_feasible": True
                })
            elif test_type == "integration":
                scenarios.append({
                    "feature": feature,
                    "scenario": f"Verify {feature} integrates with other components",
                    "test_type": test_type,
                    "estimated_test_cases": 5,
                    "priority": "high",
                    "automation_feasible": True
                })
            elif test_type == "performance":
                scenarios.append({
                    "feature": feature,
                    "scenario": f"Verify {feature} meets performance requirements",
                    "test_type": test_type,
                    "estimated_test_cases": 3,
                    "priority": "medium",
                    "automation_feasible": True
                })
        
        return scenarios
    
    def _create_test_schedule(self, scenarios: List[Dict], test_types: List[str]) -> List[Dict]:
        """Create test execution schedule."""
        schedule = []
        week = 1
        
        # Unit tests first
        if "unit" in test_types:
            schedule.append({
                "week": week,
                "phase": "Unit Testing",
                "activities": ["Execute unit tests", "Fix unit test failures"],
                "duration": "1 week"
            })
            week += 1
        
        # Integration tests
        if "integration" in test_types:
            schedule.append({
                "week": week,
                "phase": "Integration Testing",
                "activities": ["API testing", "Component integration tests"],
                "duration": "1 week"
            })
            week += 1
        
        # Functional tests
        if "functional" in test_types:
            schedule.append({
                "week": week,
                "phase": "Functional Testing",
                "activities": ["End-to-end testing", "User workflow testing"],
                "duration": "2 weeks"
            })
            week += 2
        
        # Performance and other tests
        schedule.append({
            "week": week,
            "phase": "Specialized Testing",
            "activities": ["Performance testing", "Security testing", "Usability testing"],
            "duration": "1 week"
        })
        
        return schedule
    
    def _generate_positive_tests(self, feature: str, test_type: str) -> List[Dict]:
        """Generate positive test cases."""
        tests = [
            {
                "title": f"Valid {feature} operation",
                "description": f"Verify {feature} works with valid inputs",
                "steps": [
                    "Navigate to feature",
                    "Enter valid data",
                    "Submit operation",
                    "Verify success"
                ],
                "expected": "Operation completes successfully",
                "automated": True
            },
            {
                "title": f"{feature} with typical data",
                "description": f"Test {feature} with common use case",
                "steps": [
                    "Access feature",
                    "Use typical data set",
                    "Execute operation",
                    "Check results"
                ],
                "expected": "Expected output produced",
                "automated": True
            }
        ]
        
        return tests
    
    def _generate_negative_tests(self, feature: str, test_type: str) -> List[Dict]:
        """Generate negative test cases."""
        tests = [
            {
                "title": f"Invalid input for {feature}",
                "description": f"Verify {feature} handles invalid inputs gracefully",
                "steps": [
                    "Navigate to feature",
                    "Enter invalid data",
                    "Attempt operation",
                    "Verify error handling"
                ],
                "expected": "Appropriate error message displayed",
                "automated": True
            },
            {
                "title": f"Missing required data for {feature}",
                "description": f"Test {feature} with missing required fields",
                "steps": [
                    "Access feature",
                    "Leave required fields empty",
                    "Submit operation",
                    "Check validation"
                ],
                "expected": "Validation errors shown",
                "automated": True
            }
        ]
        
        return tests
    
    def _generate_edge_cases(self, feature: str, test_type: str) -> List[Dict]:
        """Generate edge case tests."""
        tests = [
            {
                "title": f"Boundary values for {feature}",
                "description": f"Test {feature} with boundary values",
                "steps": [
                    "Navigate to feature",
                    "Enter minimum/maximum values",
                    "Execute operation",
                    "Verify behavior"
                ],
                "expected": "Correct handling of boundary values",
                "automated": True
            },
            {
                "title": f"Concurrent access to {feature}",
                "description": f"Test {feature} under concurrent usage",
                "steps": [
                    "Open multiple sessions",
                    "Access feature simultaneously",
                    "Perform operations",
                    "Check for conflicts"
                ],
                "expected": "No data corruption or conflicts",
                "automated": False
            }
        ]
        
        return tests
    
    def _identify_test_data_needs(self, test_cases: List[Dict]) -> List[str]:
        """Identify test data requirements."""
        data_needs = set()
        
        for tc in test_cases:
            if "valid data" in str(tc).lower():
                data_needs.add("Valid user accounts")
                data_needs.add("Sample valid inputs")
            if "invalid" in str(tc).lower():
                data_needs.add("Invalid data sets")
                data_needs.add("Boundary value data")
            if "typical" in str(tc).lower():
                data_needs.add("Production-like data")
        
        return list(data_needs)
    
    def _is_automation_candidate(self, test_case: Dict) -> bool:
        """Determine if test case is good automation candidate."""
        # Already marked for automation
        if test_case.get("automated", False):
            return True
        
        # Repetitive tests are good candidates
        if test_case["category"] in ["positive", "negative"]:
            return True
        
        # High priority tests should be automated
        if test_case.get("priority") == "high":
            return True
        
        return False
    
    def _assess_test_coverage(self, test_cases: List[Dict], feature: str) -> Dict[str, Any]:
        """Assess test coverage for feature."""
        return {
            "coverage_percentage": min(85 + len(test_cases), 95),
            "covered_scenarios": len(test_cases),
            "coverage_gaps": [
                "Error recovery scenarios",
                "Performance under load",
                "Cross-browser compatibility"
            ] if len(test_cases) < 10 else [],
            "coverage_strength": "Good" if len(test_cases) > 8 else "Adequate" if len(test_cases) > 5 else "Needs improvement"
        }
    
    def _assess_bug_severity(self, description: str, actual_behavior: str) -> str:
        """Assess bug severity based on description."""
        desc_lower = description.lower()
        actual_lower = actual_behavior.lower()
        
        if any(word in desc_lower + actual_lower for word in ["crash", "data loss", "security", "cannot login"]):
            return BugSeverity.CRITICAL.value
        elif any(word in desc_lower + actual_lower for word in ["error", "fail", "broken", "incorrect"]):
            return BugSeverity.HIGH.value
        elif any(word in desc_lower + actual_lower for word in ["slow", "difficult", "confusing"]):
            return BugSeverity.MEDIUM.value
        elif any(word in desc_lower + actual_lower for word in ["typo", "spacing", "color"]):
            return BugSeverity.LOW.value
        else:
            return BugSeverity.MEDIUM.value
    
    def _categorize_bug(self, description: str, actual_behavior: str) -> str:
        """Categorize bug type."""
        combined = (description + actual_behavior).lower()
        
        if any(word in combined for word in ["ui", "display", "layout", "style"]):
            return "UI/UX"
        elif any(word in combined for word in ["function", "feature", "logic"]):
            return "Functional"
        elif any(word in combined for word in ["slow", "performance", "timeout"]):
            return "Performance"
        elif any(word in combined for word in ["security", "authentication", "permission"]):
            return "Security"
        elif any(word in combined for word in ["data", "database", "storage"]):
            return "Data"
        else:
            return "General"
    
    def _determine_priority(self, severity: str, category: str) -> str:
        """Determine bug priority based on severity and category."""
        if severity == BugSeverity.CRITICAL.value:
            return "P1 - Immediate"
        elif severity == BugSeverity.HIGH.value and category in ["Security", "Data"]:
            return "P1 - Immediate"
        elif severity == BugSeverity.HIGH.value:
            return "P2 - High"
        elif severity == BugSeverity.MEDIUM.value:
            return "P3 - Medium"
        else:
            return "P4 - Low"
    
    def _analyze_bug_impact(self, severity: str, category: str) -> Dict[str, Any]:
        """Analyze bug impact."""
        impact = {
            "user_impact": "High" if severity in ["critical", "high"] else "Medium" if severity == "medium" else "Low",
            "business_impact": "Significant" if category in ["Security", "Data"] else "Moderate",
            "affected_users": "All users" if severity == "critical" else "Some users",
            "workaround_available": severity not in ["critical", "high"]
        }
        
        return impact
    
    def _suggest_fix_approach(self, description: str, category: str) -> str:
        """Suggest approach to fix bug."""
        if category == "UI/UX":
            return "Review CSS/styling and layout components"
        elif category == "Functional":
            return "Debug business logic and validate inputs"
        elif category == "Performance":
            return "Profile code and optimize bottlenecks"
        elif category == "Security":
            return "Review security controls and access patterns"
        elif category == "Data":
            return "Check data validation and database operations"
        else:
            return "Investigate root cause and implement targeted fix"
    
    def _find_related_test_cases(self, title: str, category: str) -> List[str]:
        """Find test cases related to bug."""
        # Simulated related test cases
        return [
            f"TC001 - {category} validation test",
            f"TC002 - {category} integration test",
            f"TC003 - {category} edge case test"
        ]
    
    def _analyze_root_cause(self, description: str, actual: str, category: str) -> Dict[str, str]:
        """Perform root cause analysis."""
        return {
            "probable_cause": f"{category} implementation issue",
            "contributing_factors": [
                "Insufficient validation",
                "Missing error handling",
                "Incomplete testing"
            ],
            "recommended_investigation": f"Review {category.lower()} implementation and related tests"
        }
    
    def _assess_regression_risk(self, category: str, severity: str) -> str:
        """Assess regression risk."""
        if severity in ["critical", "high"] or category in ["Security", "Data"]:
            return "high"
        elif severity == "medium":
            return "medium"
        else:
            return "low"
    
    def _identify_additional_tests(self, category: str) -> List[str]:
        """Identify additional tests needed."""
        return [
            f"Regression test for {category} functionality",
            f"Edge case tests for {category}",
            f"Integration tests with {category} dependencies"
        ]
    
    def _generate_performance_recommendations(self, results: List[Dict], issues: List[Dict]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Check for response time issues
        if any(issue["issue"] == "Response time exceeds threshold" for issue in issues):
            recommendations.append("Optimize slow queries and API calls")
            recommendations.append("Implement caching strategy")
        
        # Check for error rate issues  
        if any(issue["issue"] == "High error rate" for issue in issues):
            recommendations.append("Improve error handling and recovery")
            recommendations.append("Add circuit breakers for external dependencies")
        
        # Check resource usage
        for result in results:
            if result["metrics"]["cpu_usage"] > 80:
                recommendations.append("Optimize CPU-intensive operations")
            if result["metrics"]["memory_usage"] > 80:
                recommendations.append("Review memory usage and implement cleanup")
        
        return recommendations
