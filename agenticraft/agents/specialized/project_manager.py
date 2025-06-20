"""Project Manager Agent - Simplified for AgentiCraft.

A specialized agent for project planning, task management, and team coordination.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from agenticraft.core.agent import Agent, AgentConfig
from agenticraft.core.reasoning import ReasoningTrace, SimpleReasoning


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class ProjectManager(Agent):
    """
    Project manager agent for planning and coordinating tasks.
    
    Focuses on:
    - Project planning and timeline estimation
    - Task breakdown and prioritization
    - Resource allocation and workload balancing
    - Risk assessment and mitigation
    - Progress tracking and reporting
    """
    
    def __init__(self, name: str = "Project Manager", **kwargs):
        config = AgentConfig(
            name=name,
            role="project_manager",
            specialty="project planning and coordination",
            personality_traits={
                "organized": 0.9,
                "strategic": 0.8,
                "communicative": 0.8,
                "decisive": 0.7,
                "flexible": 0.6
            },
            **kwargs
        )
        super().__init__(config)
        
        # Project management knowledge
        self.estimation_factors = {
            "complexity": {"simple": 1.0, "medium": 1.5, "complex": 2.0},
            "uncertainty": {"low": 1.0, "medium": 1.3, "high": 1.6},
            "dependencies": {"none": 1.0, "few": 1.2, "many": 1.4}
        }
    
    async def create_project_plan(self,
                                project_name: str,
                                requirements: List[str],
                                deadline: Optional[str] = None,
                                team_size: int = 5) -> Dict[str, Any]:
        """Create a comprehensive project plan."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            f"Creating project plan for '{project_name}' with {len(requirements)} requirements"
        )
        
        # Break down requirements into tasks
        trace.add_step("task_breakdown", {
            "message": "Breaking down requirements into actionable tasks"
        })
        tasks = []
        task_id = 1
        
        for req in requirements:
            # Create main task
            main_task = {
                "id": task_id,
                "title": f"Implement: {req}",
                "description": req,
                "priority": self._assess_priority(req),
                "estimated_hours": self._estimate_task_hours(req),
                "status": TaskStatus.TODO.value,
                "dependencies": [],
                "assignee": None
            }
            tasks.append(main_task)
            task_id += 1
            
            # Add subtasks for complex requirements
            if "complex" in req.lower() or "system" in req.lower():
                subtasks = ["Design", "Implementation", "Testing", "Documentation"]
                for subtask in subtasks:
                    tasks.append({
                        "id": task_id,
                        "title": f"{subtask}: {req[:30]}...",
                        "description": f"{subtask} phase for {req}",
                        "priority": main_task["priority"],
                        "estimated_hours": main_task["estimated_hours"] / 4,
                        "status": TaskStatus.TODO.value,
                        "dependencies": [task_id - 1] if subtask != "Design" else [],
                        "assignee": None
                    })
                    task_id += 1
        
        trace.add_step("task_creation", {
            "count": len(tasks),
            "message": f"Created {len(tasks)} tasks from requirements"
        })
        
        # Calculate project timeline
        total_hours = sum(task["estimated_hours"] for task in tasks)
        parallel_factor = min(team_size, 3) * 0.7  # Parallelization efficiency
        estimated_days = (total_hours / (8 * parallel_factor))  # 8 hours per day
        
        trace.add_step("timeline_estimation", {
            "estimated_days": estimated_days,
            "message": f"Estimated project duration: {estimated_days:.1f} days"
        })
        
        # Create milestones
        milestones = self._create_milestones(tasks, estimated_days)
        
        # Assess risks
        risks = self._assess_project_risks(requirements, deadline, team_size)
        
        # Create sprint plan (2-week sprints)
        sprints = self._create_sprint_plan(tasks, team_size)
        
        trace.complete({
            "result": f"Project plan created with {len(tasks)} tasks, "
                     f"{len(milestones)} milestones, and {len(sprints)} sprints"
        })
        self.last_reasoning = trace
        
        return {
            "project_name": project_name,
            "tasks": tasks,
            "milestones": milestones,
            "sprints": sprints,
            "timeline": {
                "total_hours": total_hours,
                "estimated_days": round(estimated_days, 1),
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=estimated_days)).strftime("%Y-%m-%d")
            },
            "team": {
                "size": team_size,
                "hours_per_person": total_hours / team_size
            },
            "risks": risks,
            "critical_path": self._identify_critical_path(tasks),
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prioritize tasks using multiple criteria."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            f"Prioritizing {len(tasks)} tasks"
        )
        
        # Score each task
        scored_tasks = []
        for task in tasks:
            score = 0
            
            # Priority score (0-40 points)
            priority_scores = {
                TaskPriority.CRITICAL.value: 40,
                TaskPriority.HIGH.value: 30,
                TaskPriority.MEDIUM.value: 20,
                TaskPriority.LOW.value: 10
            }
            score += priority_scores.get(task.get("priority", "medium"), 20)
            
            # Urgency score based on deadline (0-30 points)
            if "deadline" in task:
                days_until = (datetime.fromisoformat(task["deadline"]) - datetime.now()).days
                if days_until < 3:
                    score += 30
                elif days_until < 7:
                    score += 20
                elif days_until < 14:
                    score += 10
            
            # Value/Impact score (0-20 points)
            if "value" in task:
                score += min(task["value"] / 5, 20)
            
            # Dependency score (0-10 points)
            if task.get("dependencies"):
                score += 10  # Prioritize tasks that unblock others
            
            scored_tasks.append({
                **task,
                "priority_score": score,
                "priority_rank": 0  # Will be set after sorting
            })
        
        # Sort by score
        scored_tasks.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Assign ranks
        for i, task in enumerate(scored_tasks):
            task["priority_rank"] = i + 1
        
        trace.add_step("scoring_complete", {
            "min_score": scored_tasks[-1]['priority_score'],
            "max_score": scored_tasks[0]['priority_score'],
            "message": f"Tasks prioritized with scores ranging from {scored_tasks[-1]['priority_score']} to {scored_tasks[0]['priority_score']}"
        })
        
        # Group by priority
        priority_groups = {
            "do_first": scored_tasks[:len(tasks)//4],
            "do_next": scored_tasks[len(tasks)//4:len(tasks)//2],
            "do_later": scored_tasks[len(tasks)//2:3*len(tasks)//4],
            "consider": scored_tasks[3*len(tasks)//4:]
        }
        
        trace.complete({"result": "Tasks prioritized using multi-criteria scoring"})
        self.last_reasoning = trace
        
        return {
            "prioritized_tasks": scored_tasks,
            "priority_groups": priority_groups,
            "recommendations": [
                f"Focus on top {min(3, len(scored_tasks))} tasks first",
                "Review and adjust priorities weekly",
                "Consider dependencies when scheduling"
            ],
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def allocate_resources(self,
                               tasks: List[Dict[str, Any]],
                               team_members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Allocate team members to tasks based on skills and workload."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            f"Allocating {len(team_members)} team members to {len(tasks)} tasks"
        )
        
        # Initialize workload tracking
        member_workload = {member["name"]: 0 for member in team_members}
        allocations = []
        unassigned_tasks = []
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        for task in sorted_tasks:
            # Find best match based on skills and workload
            best_match = None
            best_score = -1
            
            for member in team_members:
                # Skill match score
                skill_score = self._calculate_skill_match(task, member)
                
                # Workload balance score
                current_load = member_workload[member["name"]]
                workload_score = 1 - (current_load / 40)  # Assuming 40 hours per week
                
                # Combined score
                total_score = skill_score * 0.7 + workload_score * 0.3
                
                if total_score > best_score and current_load + task["estimated_hours"] <= 40:
                    best_score = total_score
                    best_match = member
            
            if best_match:
                allocations.append({
                    "task_id": task["id"],
                    "task_title": task["title"],
                    "assignee": best_match["name"],
                    "estimated_hours": task["estimated_hours"],
                    "match_score": best_score
                })
                member_workload[best_match["name"]] += task["estimated_hours"]
                trace.add_step("task_assignment", {
                    "task": task['title'],
                    "assignee": best_match['name'],
                    "message": f"Assigned '{task['title']}' to {best_match['name']}"
                })
            else:
                unassigned_tasks.append(task)
        
        # Calculate workload distribution
        workload_distribution = {
            name: {
                "hours": hours,
                "utilization": (hours / 40) * 100
            }
            for name, hours in member_workload.items()
        }
        
        trace.complete({
            "result": f"Allocated {len(allocations)} tasks, {len(unassigned_tasks)} remain unassigned"
        })
        self.last_reasoning = trace
        
        return {
            "allocations": allocations,
            "workload_distribution": workload_distribution,
            "unassigned_tasks": unassigned_tasks,
            "recommendations": self._generate_allocation_recommendations(
                workload_distribution, unassigned_tasks
            ),
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def track_progress(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track project progress and generate status report."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            "Analyzing project progress and generating status report"
        )
        
        tasks = project_data.get("tasks", [])
        
        # Calculate progress metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value])
        in_progress_tasks = len([t for t in tasks if t.get("status") == TaskStatus.IN_PROGRESS.value])
        blocked_tasks = len([t for t in tasks if t.get("status") == TaskStatus.BLOCKED.value])
        
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        trace.add_step("progress_calculation", {
            "completion_percentage": completion_percentage,
            "message": f"Project completion: {completion_percentage:.1f}%"
        })
        
        # Calculate velocity (if historical data available)
        velocity = completed_tasks / max(1, project_data.get("days_elapsed", 1))
        
        # Estimate completion date
        remaining_tasks = total_tasks - completed_tasks
        estimated_days_remaining = remaining_tasks / velocity if velocity > 0 else 999
        estimated_completion = datetime.now() + timedelta(days=estimated_days_remaining)
        
        # Identify risks and issues
        risks = []
        if blocked_tasks > total_tasks * 0.2:
            risks.append({
                "type": "high_blockage",
                "description": f"{blocked_tasks} tasks are blocked",
                "severity": "high",
                "mitigation": "Urgent attention needed to unblock tasks"
            })
        
        if velocity < project_data.get("target_velocity", 2):
            risks.append({
                "type": "low_velocity",
                "description": f"Current velocity ({velocity:.1f}) below target",
                "severity": "medium",
                "mitigation": "Consider adding resources or reducing scope"
            })
        
        # Generate burndown data
        burndown = {
            "ideal": [total_tasks - (i * total_tasks / project_data.get("total_days", 30)) 
                     for i in range(project_data.get("total_days", 30))],
            "actual": [total_tasks - completed_tasks]  # Simplified for this example
        }
        
        trace.complete({"result": f"Progress report generated: {completion_percentage:.1f}% complete"})
        self.last_reasoning = trace
        
        return {
            "summary": {
                "completion_percentage": round(completion_percentage, 1),
                "tasks_completed": completed_tasks,
                "tasks_in_progress": in_progress_tasks,
                "tasks_blocked": blocked_tasks,
                "tasks_remaining": total_tasks - completed_tasks
            },
            "velocity": {
                "current": round(velocity, 2),
                "target": project_data.get("target_velocity", 2),
                "trend": "improving" if velocity > 1 else "declining"
            },
            "timeline": {
                "estimated_completion": estimated_completion.strftime("%Y-%m-%d"),
                "days_remaining": round(estimated_days_remaining),
                "on_track": estimated_completion <= datetime.fromisoformat(
                    project_data.get("deadline", "2099-12-31")
                )
            },
            "risks": risks,
            "burndown": burndown,
            "recommendations": self._generate_progress_recommendations(
                completion_percentage, velocity, risks
            ),
            "reasoning": reasoning.format_trace(trace)
        }
    
    def _assess_priority(self, requirement: str) -> str:
        """Assess task priority based on keywords."""
        requirement_lower = requirement.lower()
        
        if any(word in requirement_lower for word in ["critical", "urgent", "security", "bug"]):
            return TaskPriority.CRITICAL.value
        elif any(word in requirement_lower for word in ["important", "core", "main"]):
            return TaskPriority.HIGH.value
        elif any(word in requirement_lower for word in ["enhancement", "improvement"]):
            return TaskPriority.MEDIUM.value
        else:
            return TaskPriority.LOW.value
    
    def _estimate_task_hours(self, requirement: str) -> float:
        """Estimate task hours based on complexity."""
        base_hours = 8  # Base estimate
        
        # Adjust based on keywords
        if any(word in requirement.lower() for word in ["simple", "minor", "small"]):
            return base_hours * 0.5
        elif any(word in requirement.lower() for word in ["complex", "system", "integration"]):
            return base_hours * 2
        elif any(word in requirement.lower() for word in ["large", "major", "comprehensive"]):
            return base_hours * 3
        
        return base_hours
    
    def _create_milestones(self, tasks: List[Dict], total_days: float) -> List[Dict]:
        """Create project milestones."""
        milestones = []
        
        # Divide project into phases
        phases = [
            ("Planning & Design", 0.2),
            ("Core Development", 0.5),
            ("Testing & Integration", 0.2),
            ("Deployment & Documentation", 0.1)
        ]
        
        cumulative_days = 0
        for phase_name, phase_portion in phases:
            phase_days = total_days * phase_portion
            cumulative_days += phase_days
            
            milestones.append({
                "name": phase_name,
                "target_date": (datetime.now() + timedelta(days=cumulative_days)).strftime("%Y-%m-%d"),
                "deliverables": f"Complete {phase_name.lower()} phase",
                "success_criteria": f"All {phase_name.lower()} tasks completed and approved"
            })
        
        return milestones
    
    def _assess_project_risks(self, requirements: List[str], deadline: str, team_size: int) -> List[Dict]:
        """Assess project risks."""
        risks = []
        
        # Scope risks
        if len(requirements) > team_size * 5:
            risks.append({
                "type": "scope",
                "description": "Large scope relative to team size",
                "probability": "high",
                "impact": "high",
                "mitigation": "Consider phased delivery or increasing team size"
            })
        
        # Technical risks
        if any("integration" in req.lower() or "migration" in req.lower() for req in requirements):
            risks.append({
                "type": "technical",
                "description": "Complex integrations or migrations involved",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Plan for extensive testing and rollback procedures"
            })
        
        # Timeline risks
        if deadline:
            days_available = (datetime.fromisoformat(deadline) - datetime.now()).days
            if days_available < len(requirements) * 2:
                risks.append({
                    "type": "timeline",
                    "description": "Tight deadline relative to scope",
                    "probability": "high",
                    "impact": "medium",
                    "mitigation": "Prioritize MVP features and plan for post-launch updates"
                })
        
        return risks
    
    def _create_sprint_plan(self, tasks: List[Dict], team_size: int) -> List[Dict]:
        """Create sprint plan."""
        sprint_capacity = team_size * 40 * 2  # 2 weeks, 40 hours per week
        sprints = []
        current_sprint_tasks = []
        current_sprint_hours = 0
        sprint_number = 1
        
        for task in tasks:
            if current_sprint_hours + task["estimated_hours"] <= sprint_capacity:
                current_sprint_tasks.append(task["id"])
                current_sprint_hours += task["estimated_hours"]
            else:
                # Complete current sprint
                sprints.append({
                    "sprint_number": sprint_number,
                    "task_ids": current_sprint_tasks,
                    "total_hours": current_sprint_hours,
                    "capacity_utilization": (current_sprint_hours / sprint_capacity) * 100
                })
                
                # Start new sprint
                sprint_number += 1
                current_sprint_tasks = [task["id"]]
                current_sprint_hours = task["estimated_hours"]
        
        # Add final sprint
        if current_sprint_tasks:
            sprints.append({
                "sprint_number": sprint_number,
                "task_ids": current_sprint_tasks,
                "total_hours": current_sprint_hours,
                "capacity_utilization": (current_sprint_hours / sprint_capacity) * 100
            })
        
        return sprints
    
    def _identify_critical_path(self, tasks: List[Dict]) -> List[int]:
        """Identify critical path through tasks."""
        # Simplified critical path - tasks with dependencies
        critical_tasks = []
        for task in tasks:
            if task.get("dependencies") or any(t.get("dependencies", []) == [task["id"]] for t in tasks):
                critical_tasks.append(task["id"])
        
        return critical_tasks[:5]  # Return top 5 critical tasks
    
    def _calculate_skill_match(self, task: Dict, member: Dict) -> float:
        """Calculate skill match between task and team member."""
        # Simplified skill matching
        task_keywords = task.get("title", "").lower().split()
        member_skills = member.get("skills", [])
        
        matches = sum(1 for skill in member_skills 
                     if any(keyword in skill.lower() for keyword in task_keywords))
        
        return min(matches / max(len(member_skills), 1), 1.0)
    
    def _generate_allocation_recommendations(self, 
                                          workload: Dict, 
                                          unassigned: List) -> List[str]:
        """Generate resource allocation recommendations."""
        recommendations = []
        
        # Check for overallocation
        overallocated = [name for name, data in workload.items() 
                        if data["utilization"] > 100]
        if overallocated:
            recommendations.append(
                f"Team members overallocated: {', '.join(overallocated)}. "
                "Consider redistributing tasks."
            )
        
        # Check for underutilization
        underutilized = [name for name, data in workload.items() 
                        if data["utilization"] < 60]
        if underutilized:
            recommendations.append(
                f"Team members underutilized: {', '.join(underutilized)}. "
                "Can take on additional tasks."
            )
        
        # Unassigned tasks
        if unassigned:
            recommendations.append(
                f"{len(unassigned)} tasks remain unassigned. "
                "Consider adding team members or extending timeline."
            )
        
        return recommendations
    
    def _generate_progress_recommendations(self, 
                                         completion: float, 
                                         velocity: float,
                                         risks: List[Dict]) -> List[str]:
        """Generate progress recommendations."""
        recommendations = []
        
        if completion < 50 and velocity < 2:
            recommendations.append(
                "Project progressing slowly. Consider daily standups to identify blockers."
            )
        
        if any(r["severity"] == "high" for r in risks):
            recommendations.append(
                "High-severity risks identified. Schedule risk review meeting."
            )
        
        if velocity > 3:
            recommendations.append(
                "Team performing well. Consider documenting successful practices."
            )
        
        return recommendations
