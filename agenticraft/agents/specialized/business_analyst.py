"""Business Analyst Agent - Created for AgentiCraft.

A specialized agent for requirements analysis, process optimization,
and stakeholder communication.
"""

from typing import Dict, List, Optional, Any, Tuple
from agenticraft.core.agent import Agent, AgentConfig
from agenticraft.core.reasoning import ReasoningTrace, SimpleReasoning


class BusinessAnalyst(Agent):
    """
    Business analyst agent for requirements gathering and process analysis.
    
    Focuses on:
    - Requirements elicitation and documentation
    - Process mapping and optimization
    - Stakeholder analysis and communication
    - Gap analysis and solution design
    - Business case development
    """
    
    def __init__(self, name: str = "Business Analyst", **kwargs):
        config = AgentConfig(
            name=name,
            role="business_analyst",
            specialty="requirements analysis and process optimization",
            personality_traits={
                "analytical": 0.9,
                "communicative": 0.9,
                "detail_oriented": 0.8,
                "diplomatic": 0.7,
                "creative": 0.6
            },
            **kwargs
        )
        super().__init__(config)
        
        # Business analysis templates
        self.requirement_categories = [
            "functional",
            "non_functional",
            "business",
            "technical",
            "regulatory"
        ]
        
        self.analysis_techniques = [
            "SWOT Analysis",
            "Gap Analysis",
            "Root Cause Analysis",
            "Cost-Benefit Analysis",
            "Process Mapping"
        ]
    
    async def analyze_requirements(self,
                                 project_description: str,
                                 stakeholders: List[str] = None) -> Dict[str, Any]:
        """Analyze and structure project requirements."""
        thought = SimpleReasoning(
            initial_thought=f"Analyzing requirements for project: {project_description[:50]}..."
        )
        
        # Extract key concepts from description
        thought.add_thought("Identifying key business needs and objectives")
        
        # Parse requirements from description
        requirements = {
            "functional": [],
            "non_functional": [],
            "business": [],
            "technical": [],
            "regulatory": []
        }
        
        # Analyze for functional requirements
        functional_keywords = ["feature", "capability", "function", "process", "workflow"]
        if any(keyword in project_description.lower() for keyword in functional_keywords):
            requirements["functional"].extend([
                {
                    "id": "FR001",
                    "title": "Core functionality implementation",
                    "description": "System must provide the described core features",
                    "priority": "high",
                    "acceptance_criteria": [
                        "Feature works as described",
                        "User can complete primary workflow",
                        "System responds within 2 seconds"
                    ]
                },
                {
                    "id": "FR002",
                    "title": "User interface requirements",
                    "description": "Intuitive interface for all user types",
                    "priority": "high",
                    "acceptance_criteria": [
                        "UI follows design standards",
                        "All functions accessible within 3 clicks",
                        "Mobile responsive design"
                    ]
                }
            ])
            thought.add_thought(f"Identified {len(requirements['functional'])} functional requirements")
        
        # Analyze for non-functional requirements
        requirements["non_functional"].extend([
            {
                "id": "NFR001",
                "category": "performance",
                "requirement": "System response time < 2 seconds for 95% of requests",
                "measurement": "Response time monitoring"
            },
            {
                "id": "NFR002",
                "category": "security",
                "requirement": "All data encrypted in transit and at rest",
                "measurement": "Security audit compliance"
            },
            {
                "id": "NFR003",
                "category": "scalability",
                "requirement": "Support 10,000 concurrent users",
                "measurement": "Load testing results"
            }
        ])
        
        # Business requirements based on description
        requirements["business"].append({
            "id": "BR001",
            "objective": "Improve operational efficiency",
            "success_metric": "20% reduction in process time",
            "stakeholders": stakeholders or ["Business Users", "Management"]
        })
        
        # Create requirements traceability matrix
        traceability_matrix = self._create_traceability_matrix(requirements)
        
        # Identify gaps and risks
        gaps = self._identify_requirement_gaps(requirements, project_description)
        
        thought.set_final_decision(
            f"Analyzed requirements: {sum(len(reqs) for reqs in requirements.values())} total requirements identified"
        )
        self.last_reasoning = thought
        
        return {
            "requirements": requirements,
            "traceability_matrix": traceability_matrix,
            "gaps": gaps,
            "stakeholder_impact": self._analyze_stakeholder_impact(requirements, stakeholders),
            "recommended_next_steps": [
                "Validate requirements with stakeholders",
                "Prioritize requirements with product owner",
                "Create detailed user stories",
                "Define test scenarios for each requirement"
            ],
            "reasoning": thought.to_dict()
        }
    
    async def create_process_map(self,
                               process_name: str,
                               current_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create process map and optimization recommendations."""
        thought = SimpleReasoning(
            initial_thought=f"Mapping process: {process_name}"
        )
        
        # Define process steps
        if current_state and "steps" in current_state:
            process_steps = current_state["steps"]
            thought.add_thought(f"Working with {len(process_steps)} existing process steps")
        else:
            # Create generic process template
            process_steps = [
                {"id": 1, "name": "Initiation", "duration": "30 min", "actors": ["User"]},
                {"id": 2, "name": "Processing", "duration": "2 hours", "actors": ["System"]},
                {"id": 3, "name": "Review", "duration": "1 hour", "actors": ["Reviewer"]},
                {"id": 4, "name": "Approval", "duration": "30 min", "actors": ["Manager"]},
                {"id": 5, "name": "Completion", "duration": "15 min", "actors": ["System"]}
            ]
            thought.add_thought("Created generic process template")
        
        # Analyze process
        total_duration = self._calculate_process_duration(process_steps)
        bottlenecks = self._identify_bottlenecks(process_steps)
        
        # Create optimized process
        optimized_steps = self._optimize_process(process_steps)
        optimized_duration = self._calculate_process_duration(optimized_steps)
        
        improvement_percentage = ((total_duration - optimized_duration) / total_duration) * 100
        thought.add_thought(f"Process optimization achieved {improvement_percentage:.1f}% time reduction")
        
        # Generate BPMN-like notation
        process_diagram = {
            "nodes": [
                {
                    "id": step["id"],
                    "type": "task" if step["name"] != "Approval" else "gateway",
                    "label": step["name"],
                    "actors": step.get("actors", [])
                }
                for step in process_steps
            ],
            "edges": [
                {"from": i, "to": i + 1}
                for i in range(1, len(process_steps))
            ]
        }
        
        thought.set_final_decision(f"Process map created with {improvement_percentage:.1f}% optimization potential")
        self.last_reasoning = thought
        
        return {
            "current_process": {
                "steps": process_steps,
                "total_duration": f"{total_duration} minutes",
                "bottlenecks": bottlenecks
            },
            "optimized_process": {
                "steps": optimized_steps,
                "total_duration": f"{optimized_duration} minutes",
                "improvements": self._describe_improvements(process_steps, optimized_steps)
            },
            "process_diagram": process_diagram,
            "metrics": {
                "efficiency_gain": f"{improvement_percentage:.1f}%",
                "steps_eliminated": len(process_steps) - len(optimized_steps),
                "automation_opportunities": len([s for s in optimized_steps if "automated" in s.get("name", "").lower()])
            },
            "recommendations": [
                "Automate approval workflow for standard cases",
                "Implement parallel processing where possible",
                "Create process dashboards for real-time monitoring",
                "Train staff on optimized process"
            ],
            "reasoning": thought.to_dict()
        }
    
    async def perform_gap_analysis(self,
                                 current_state: Dict[str, Any],
                                 desired_state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform gap analysis between current and desired states."""
        thought = SimpleReasoning(
            initial_thought="Performing gap analysis between current and desired states"
        )
        
        gaps = []
        gap_id = 1
        
        # Analyze capability gaps
        current_capabilities = set(current_state.get("capabilities", []))
        desired_capabilities = set(desired_state.get("capabilities", []))
        
        for capability in desired_capabilities - current_capabilities:
            gaps.append({
                "id": f"GAP{gap_id:03d}",
                "type": "capability",
                "description": f"Missing capability: {capability}",
                "impact": "high",
                "effort": "medium",
                "priority": 1
            })
            gap_id += 1
        
        thought.add_thought(f"Identified {len(gaps)} capability gaps")
        
        # Analyze process gaps
        if "processes" in current_state and "processes" in desired_state:
            process_gaps = self._analyze_process_gaps(
                current_state["processes"],
                desired_state["processes"]
            )
            gaps.extend(process_gaps)
            thought.add_thought(f"Identified {len(process_gaps)} process gaps")
        
        # Analyze technology gaps
        if "technology" in current_state and "technology" in desired_state:
            tech_gaps = self._analyze_technology_gaps(
                current_state["technology"],
                desired_state["technology"]
            )
            gaps.extend(tech_gaps)
        
        # Create bridging strategies
        strategies = self._create_bridging_strategies(gaps)
        
        # Calculate implementation roadmap
        roadmap = self._create_gap_closure_roadmap(gaps, strategies)
        
        thought.set_final_decision(f"Gap analysis complete: {len(gaps)} gaps identified with bridging strategies")
        self.last_reasoning = thought
        
        return {
            "gaps_identified": gaps,
            "gap_categories": self._categorize_gaps(gaps),
            "bridging_strategies": strategies,
            "implementation_roadmap": roadmap,
            "estimated_effort": self._estimate_total_effort(gaps),
            "risk_assessment": self._assess_gap_risks(gaps),
            "quick_wins": [gap for gap in gaps if gap.get("effort") == "low" and gap.get("impact") == "high"],
            "reasoning": thought.to_dict()
        }
    
    async def create_business_case(self,
                                 project_name: str,
                                 investment: float,
                                 benefits: List[str]) -> Dict[str, Any]:
        """Create business case for project or initiative."""
        thought = SimpleReasoning(
            initial_thought=f"Creating business case for {project_name}"
        )
        
        # Quantify benefits
        quantified_benefits = []
        total_benefit_value = 0
        
        for benefit in benefits:
            # Estimate value (simplified)
            if "efficiency" in benefit.lower():
                value = investment * 0.3  # 30% efficiency gain
                quantified_benefits.append({
                    "description": benefit,
                    "type": "efficiency",
                    "annual_value": value,
                    "confidence": "medium"
                })
            elif "revenue" in benefit.lower():
                value = investment * 0.5  # 50% revenue impact
                quantified_benefits.append({
                    "description": benefit,
                    "type": "revenue",
                    "annual_value": value,
                    "confidence": "medium"
                })
            else:
                value = investment * 0.2  # 20% general benefit
                quantified_benefits.append({
                    "description": benefit,
                    "type": "strategic",
                    "annual_value": value,
                    "confidence": "low"
                })
            total_benefit_value += value
        
        thought.add_thought(f"Quantified {len(benefits)} benefits worth ${total_benefit_value:,.0f} annually")
        
        # Calculate ROI
        roi = ((total_benefit_value - investment) / investment) * 100
        payback_period = investment / total_benefit_value * 12  # months
        
        # Risk analysis
        risks = [
            {"risk": "Implementation delays", "probability": "medium", "impact": "medium", "mitigation": "Phased rollout approach"},
            {"risk": "User adoption challenges", "probability": "medium", "impact": "high", "mitigation": "Comprehensive training program"},
            {"risk": "Technical complexity", "probability": "low", "impact": "high", "mitigation": "Experienced implementation team"}
        ]
        
        # Create executive summary
        executive_summary = f"""
{project_name} represents a strategic investment of ${investment:,.0f} that will deliver
annual benefits of ${total_benefit_value:,.0f} through {len(benefits)} key value drivers.
With an ROI of {roi:.0f}% and a payback period of {payback_period:.1f} months,
this initiative aligns with organizational objectives and provides significant value.
"""
        
        thought.set_final_decision(f"Business case complete: {roi:.0f}% ROI, {payback_period:.1f} month payback")
        self.last_reasoning = thought
        
        return {
            "executive_summary": executive_summary.strip(),
            "financial_analysis": {
                "investment": investment,
                "annual_benefits": total_benefit_value,
                "roi": f"{roi:.0f}%",
                "payback_period": f"{payback_period:.1f} months",
                "npv_5_year": total_benefit_value * 3.5 - investment  # Simplified NPV
            },
            "benefits": quantified_benefits,
            "risks": risks,
            "implementation_approach": {
                "phase_1": "Planning and design (2 months)",
                "phase_2": "Development and testing (4 months)",
                "phase_3": "Rollout and training (2 months)",
                "phase_4": "Optimization and scaling (ongoing)"
            },
            "success_metrics": [
                "User adoption rate > 80%",
                "Process efficiency improvement > 25%",
                "Error reduction > 50%",
                "Customer satisfaction increase > 15%"
            ],
            "recommendation": "PROCEED" if roi > 20 else "REVIEW",
            "reasoning": thought.to_dict()
        }
    
    def _create_traceability_matrix(self, requirements: Dict) -> List[Dict]:
        """Create requirements traceability matrix."""
        matrix = []
        for category, reqs in requirements.items():
            for req in reqs:
                matrix.append({
                    "requirement_id": req.get("id", f"{category[:3].upper()}{len(matrix)+1:03d}"),
                    "category": category,
                    "title": req.get("title", req.get("requirement", req.get("objective", ""))),
                    "source": "Stakeholder Interview",
                    "test_cases": f"TC_{req.get('id', len(matrix)+1)}",
                    "status": "defined"
                })
        return matrix
    
    def _identify_requirement_gaps(self, requirements: Dict, description: str) -> List[str]:
        """Identify potential gaps in requirements."""
        gaps = []
        
        # Check for missing requirement categories
        if not requirements["non_functional"]:
            gaps.append("Non-functional requirements need further definition")
        
        if not requirements["regulatory"]:
            gaps.append("Regulatory compliance requirements should be investigated")
        
        # Check for common missing elements
        if "integration" in description.lower() and not any(
            "integration" in str(req).lower() for reqs in requirements.values() for req in reqs
        ):
            gaps.append("Integration requirements need to be specified")
        
        if "data" in description.lower() and not any(
            "data" in str(req).lower() for reqs in requirements.values() for req in reqs
        ):
            gaps.append("Data management requirements need clarification")
        
        return gaps
    
    def _analyze_stakeholder_impact(self, requirements: Dict, stakeholders: List[str]) -> Dict[str, List[str]]:
        """Analyze impact on stakeholders."""
        if not stakeholders:
            stakeholders = ["End Users", "Management", "IT Department"]
        
        impact = {}
        for stakeholder in stakeholders:
            impacts = []
            
            if stakeholder.lower() == "end users":
                impacts = ["New interface to learn", "Improved efficiency", "Training required"]
            elif "management" in stakeholder.lower():
                impacts = ["Better reporting capabilities", "ROI tracking needed", "Change management"]
            elif "it" in stakeholder.lower():
                impacts = ["New system to maintain", "Integration work", "Security considerations"]
            else:
                impacts = ["Process changes", "Potential workflow adjustments"]
            
            impact[stakeholder] = impacts
        
        return impact
    
    def _calculate_process_duration(self, steps: List[Dict]) -> int:
        """Calculate total process duration in minutes."""
        total = 0
        for step in steps:
            duration_str = step.get("duration", "0 min")
            if "hour" in duration_str:
                hours = float(duration_str.split()[0])
                total += hours * 60
            elif "min" in duration_str:
                minutes = float(duration_str.split()[0])
                total += minutes
        return int(total)
    
    def _identify_bottlenecks(self, steps: List[Dict]) -> List[Dict]:
        """Identify process bottlenecks."""
        bottlenecks = []
        for step in steps:
            duration_str = step.get("duration", "0 min")
            duration_min = 0
            
            if "hour" in duration_str:
                duration_min = float(duration_str.split()[0]) * 60
            elif "min" in duration_str:
                duration_min = float(duration_str.split()[0])
            
            if duration_min > 60:  # More than 1 hour
                bottlenecks.append({
                    "step": step["name"],
                    "duration": duration_str,
                    "reason": "Long processing time",
                    "suggestion": "Consider automation or parallel processing"
                })
        
        return bottlenecks
    
    def _optimize_process(self, steps: List[Dict]) -> List[Dict]:
        """Optimize process steps."""
        optimized = []
        
        for step in steps:
            # Skip redundant review steps
            if "review" in step["name"].lower() and any("approval" in s["name"].lower() for s in steps):
                continue
            
            # Optimize duration
            optimized_step = step.copy()
            if "processing" in step["name"].lower():
                optimized_step["duration"] = "30 min"
                optimized_step["name"] += " (automated)"
            
            optimized.append(optimized_step)
        
        return optimized
    
    def _describe_improvements(self, original: List[Dict], optimized: List[Dict]) -> List[str]:
        """Describe process improvements."""
        improvements = []
        
        if len(optimized) < len(original):
            improvements.append(f"Eliminated {len(original) - len(optimized)} redundant steps")
        
        automated_count = len([s for s in optimized if "automated" in s.get("name", "").lower()])
        if automated_count > 0:
            improvements.append(f"Automated {automated_count} manual processes")
        
        improvements.append("Reduced overall process complexity")
        
        return improvements
    
    def _analyze_process_gaps(self, current: List[str], desired: List[str]) -> List[Dict]:
        """Analyze gaps between current and desired processes."""
        gaps = []
        gap_id = 100
        
        for process in desired:
            if process not in current:
                gaps.append({
                    "id": f"GAP{gap_id:03d}",
                    "type": "process",
                    "description": f"Missing process: {process}",
                    "impact": "medium",
                    "effort": "medium",
                    "priority": 2
                })
                gap_id += 1
        
        return gaps
    
    def _analyze_technology_gaps(self, current: List[str], desired: List[str]) -> List[Dict]:
        """Analyze technology gaps."""
        gaps = []
        gap_id = 200
        
        for tech in desired:
            if tech not in current:
                gaps.append({
                    "id": f"GAP{gap_id:03d}",
                    "type": "technology",
                    "description": f"Technology gap: {tech}",
                    "impact": "high",
                    "effort": "high",
                    "priority": 1
                })
                gap_id += 1
        
        return gaps
    
    def _create_bridging_strategies(self, gaps: List[Dict]) -> Dict[str, List[str]]:
        """Create strategies to bridge identified gaps."""
        strategies = {
            "capability": [
                "Develop training programs",
                "Hire specialized talent",
                "Partner with external experts"
            ],
            "process": [
                "Document and standardize processes",
                "Implement process automation",
                "Establish process governance"
            ],
            "technology": [
                "Evaluate and select solutions",
                "Plan phased implementation",
                "Ensure integration capabilities"
            ]
        }
        
        return strategies
    
    def _create_gap_closure_roadmap(self, gaps: List[Dict], strategies: Dict) -> List[Dict]:
        """Create roadmap for closing gaps."""
        roadmap = [
            {
                "phase": "Assessment (Month 1-2)",
                "activities": ["Detailed gap analysis", "Stakeholder alignment", "Resource planning"],
                "deliverables": ["Gap analysis report", "Implementation plan"]
            },
            {
                "phase": "Quick Wins (Month 3-4)",
                "activities": ["Address high-impact, low-effort gaps", "Build momentum"],
                "deliverables": ["Initial improvements", "Success stories"]
            },
            {
                "phase": "Major Implementation (Month 5-10)",
                "activities": ["Technology deployment", "Process transformation", "Training rollout"],
                "deliverables": ["New systems live", "Trained staff"]
            },
            {
                "phase": "Optimization (Month 11-12)",
                "activities": ["Fine-tuning", "Measure results", "Continuous improvement"],
                "deliverables": ["Performance reports", "Lessons learned"]
            }
        ]
        
        return roadmap
    
    def _categorize_gaps(self, gaps: List[Dict]) -> Dict[str, int]:
        """Categorize gaps by type."""
        categories = {}
        for gap in gaps:
            gap_type = gap.get("type", "other")
            categories[gap_type] = categories.get(gap_type, 0) + 1
        return categories
    
    def _estimate_total_effort(self, gaps: List[Dict]) -> Dict[str, Any]:
        """Estimate total effort to close gaps."""
        effort_mapping = {"low": 1, "medium": 3, "high": 5}
        total_effort = sum(effort_mapping.get(gap.get("effort", "medium"), 3) for gap in gaps)
        
        return {
            "total_person_months": total_effort,
            "recommended_team_size": max(3, total_effort // 6),
            "estimated_duration": f"{total_effort // 3} months"
        }
    
    def _assess_gap_risks(self, gaps: List[Dict]) -> List[Dict]:
        """Assess risks associated with gaps."""
        risks = []
        
        high_priority_gaps = [g for g in gaps if g.get("priority") == 1]
        if len(high_priority_gaps) > 5:
            risks.append({
                "risk": "Too many high-priority gaps",
                "impact": "Resource constraints",
                "mitigation": "Phased approach with clear priorities"
            })
        
        high_effort_gaps = [g for g in gaps if g.get("effort") == "high"]
        if len(high_effort_gaps) > 3:
            risks.append({
                "risk": "Multiple high-effort initiatives",
                "impact": "Extended timeline",
                "mitigation": "Consider parallel workstreams"
            })
        
        return risks
