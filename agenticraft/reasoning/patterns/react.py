"""ReAct (Reason + Act) pattern implementation.

This module implements the ReAct pattern which interleaves reasoning (thought)
with acting (action) and observing results, creating a dynamic problem-solving loop.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from agenticraft.core.reasoning import BaseReasoning, ReasoningTrace
from agenticraft.core.tool import BaseTool


class StepType(Enum):
    """Type of step in ReAct sequence."""

    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    CONCLUSION = "conclusion"


@dataclass
class ReActStep:
    """A single step in the ReAct reasoning process.

    Attributes:
        step_number: Sequential number of this step
        step_type: Type of step (thought, action, observation)
        content: The actual content of the step
        tool_used: Tool name if action step
        tool_result: Result from tool if action step
        confidence: Confidence in this step
        requires_revision: Whether this step needs revision
        timestamp: When this step was created
    """

    step_number: int
    step_type: StepType
    content: str
    tool_used: str | None = None
    tool_result: Any | None = None
    confidence: float = 1.0
    requires_revision: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "content": self.content,
            "tool_used": self.tool_used,
            "tool_result": str(self.tool_result) if self.tool_result else None,
            "confidence": self.confidence,
            "requires_revision": self.requires_revision,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class ReActReasoning(BaseReasoning):
    """Implements ReAct (Reason + Act) pattern.

    This pattern alternates between:
    1. Thought: Reasoning about the current state
    2. Action: Taking an action (usually calling a tool)
    3. Observation: Observing the result of the action

    The cycle continues until a solution is found or max steps reached.

    Example:
        >>> tools = {"search": SearchTool(), "calculate": CalculatorTool()}
        >>> react = ReActReasoning(tools=tools, max_steps=10)
        >>> trace = await react.think(
        ...     "What is the population density of Tokyo?",
        ...     context={"year": 2024}
        ... )
        >>> print(react.get_solution())
    """

    def __init__(
        self,
        tools: dict[str, BaseTool] | None = None,
        max_steps: int = 15,
        max_retries: int = 2,
        reflection_frequency: int = 3,
    ):
        """Initialize ReAct reasoning.

        Args:
            tools: Dictionary of available tools
            max_steps: Maximum number of reasoning steps
            max_retries: Maximum retries for failed actions
            reflection_frequency: How often to reflect on progress
        """
        super().__init__(
            name="react",
            description="Reasoning interleaved with actions and observations",
        )
        self.tools = tools or {}
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.reflection_frequency = reflection_frequency

        self.steps: list[ReActStep] = []
        self.step_counter = 0
        self.solution_found = False
        self.current_context: dict[str, Any] = {}

    async def think(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> ReasoningTrace:
        """Generate ReAct reasoning for a problem.

        Args:
            problem: The problem to solve
            context: Additional context

        Returns:
            ReasoningTrace containing the reasoning process
        """
        trace = ReasoningTrace()
        self._reset()
        self.current_context = context or {}

        # Initial problem analysis
        trace.add_step(
            "problem_analysis",
            {
                "problem": problem,
                "available_tools": list(self.tools.keys()),
                "context": self.current_context,
            },
        )

        # Main ReAct loop
        while self.step_counter < self.max_steps and not self.solution_found:
            # Thought step
            thought = await self._generate_thought(problem)
            self.steps.append(thought)
            trace.add_step(f"thought_{thought.step_number}", thought.to_dict())

            # Check if we have a solution
            if self._is_solution_in_thought(thought):
                self.solution_found = True
                conclusion = await self._generate_conclusion()
                self.steps.append(conclusion)
                trace.add_step("conclusion", conclusion.to_dict())
                break

            # Determine if action is needed
            action_needed, action_type = self._determine_action_needed(thought)

            if action_needed:
                # Action step
                action = await self._generate_action(thought, action_type)
                if action:
                    self.steps.append(action)
                    trace.add_step(f"action_{action.step_number}", action.to_dict())

                    # Observation step
                    observation = await self._observe_action_result(action)
                    self.steps.append(observation)
                    trace.add_step(
                        f"observation_{observation.step_number}", observation.to_dict()
                    )

                    # Update context with observation
                    self._update_context(observation)

            # Periodic reflection
            if (
                self.step_counter % self.reflection_frequency == 0
                and self.step_counter > 0
            ):
                reflection = await self._reflect_on_progress()
                self.steps.append(reflection)
                trace.add_step(
                    f"reflection_{reflection.step_number}", reflection.to_dict()
                )

                # Check if we need to revise approach
                if reflection.requires_revision:
                    trace.add_step(
                        "approach_revision",
                        {
                            "reason": "Reflection indicated need for revision",
                            "step": self.step_counter,
                        },
                    )

        # Final analysis
        if not self.solution_found:
            trace.add_step(
                "max_steps_reached",
                {"steps_taken": self.step_counter, "max_steps": self.max_steps},
            )

        # Generate summary
        summary = self._generate_summary()
        trace.add_step("reasoning_summary", summary)

        return trace

    def _reset(self):
        """Reset reasoning state for new problem."""
        self.steps.clear()
        self.step_counter = 0
        self.solution_found = False
        self.current_context.clear()

    async def _generate_thought(self, problem: str) -> ReActStep:
        """Generate a thought step.

        Args:
            problem: The problem being solved

        Returns:
            A thought step
        """
        self.step_counter += 1

        # Analyze current state
        previous_observations = [
            step for step in self.steps if step.step_type == StepType.OBSERVATION
        ]

        # In real implementation, this would use an LLM
        if not previous_observations:
            # Initial thought
            thought_content = (
                f"To solve '{problem}', I need to break it down and gather information."
            )
        else:
            # Subsequent thoughts based on observations
            last_obs = previous_observations[-1]
            thought_content = f"Based on the observation that {last_obs.content[:50]}..., I should next..."

        return ReActStep(
            step_number=self.step_counter,
            step_type=StepType.THOUGHT,
            content=thought_content,
            confidence=0.8,
        )

    def _is_solution_in_thought(self, thought: ReActStep) -> bool:
        """Check if the thought contains or indicates a solution.

        Args:
            thought: The thought step to check

        Returns:
            True if solution is found
        """
        solution_indicators = [
            "the answer is",
            "therefore",
            "in conclusion",
            "the solution is",
            "finally",
        ]

        thought_lower = thought.content.lower()
        return any(indicator in thought_lower for indicator in solution_indicators)

    def _determine_action_needed(self, thought: ReActStep) -> tuple[bool, str | None]:
        """Determine if action is needed based on thought.

        Args:
            thought: The current thought

        Returns:
            Tuple of (action_needed, action_type)
        """
        thought_lower = thought.content.lower()

        # Simple heuristics for action determination
        if "need to search" in thought_lower or "look up" in thought_lower:
            return True, "search"
        elif "calculate" in thought_lower or "compute" in thought_lower:
            return True, "calculate"
        elif "verify" in thought_lower or "check" in thought_lower:
            return True, "verify"
        elif "more information" in thought_lower:
            return True, "search"

        return False, None

    async def _generate_action(
        self, thought: ReActStep, action_type: str
    ) -> ReActStep | None:
        """Generate an action based on thought.

        Args:
            thought: The thought leading to this action
            action_type: Type of action to take

        Returns:
            Action step or None if no appropriate action
        """
        self.step_counter += 1

        # Map action type to tool
        tool_mapping = {
            "search": "search",
            "calculate": "calculator",
            "verify": "search",
            # Add more mappings as needed
        }

        tool_name = tool_mapping.get(action_type)
        if not tool_name or tool_name not in self.tools:
            # No appropriate tool available
            return None

        # Generate action parameters based on thought
        # In real implementation, this would use an LLM
        action_params = self._extract_action_params(thought.content, action_type)

        return ReActStep(
            step_number=self.step_counter,
            step_type=StepType.ACTION,
            content=f"Using {tool_name} tool with params: {action_params}",
            tool_used=tool_name,
            metadata={"params": action_params},
        )

    def _extract_action_params(self, thought: str, action_type: str) -> dict[str, Any]:
        """Extract parameters for action from thought.

        Args:
            thought: The thought content
            action_type: Type of action

        Returns:
            Parameters for the action
        """
        # Simplified parameter extraction
        if action_type == "search":
            # Extract what to search for
            import re

            search_patterns = [
                r"search for (.*?)(?:\.|,|$)",
                r"look up (.*?)(?:\.|,|$)",
                r"find (.*?)(?:\.|,|$)",
            ]

            for pattern in search_patterns:
                match = re.search(pattern, thought.lower())
                if match:
                    return {"query": match.group(1).strip()}

            return {"query": "relevant information"}

        elif action_type == "calculate":
            # Extract calculation
            return {"expression": "sample calculation"}

        return {}

    async def _observe_action_result(self, action: ReActStep) -> ReActStep:
        """Execute action and observe result.

        Args:
            action: The action to execute

        Returns:
            Observation step with results
        """
        self.step_counter += 1

        tool_name = action.tool_used
        tool = self.tools.get(tool_name)

        if not tool:
            return ReActStep(
                step_number=self.step_counter,
                step_type=StepType.OBSERVATION,
                content=f"Error: Tool '{tool_name}' not available",
                confidence=0.0,
                requires_revision=True,
            )

        try:
            # Execute tool with retry logic
            params = action.metadata.get("params", {})
            result = None

            for attempt in range(self.max_retries):
                try:
                    result = await tool.arun(**params)
                    break
                except Exception:
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(1)  # Brief pause before retry

            return ReActStep(
                step_number=self.step_counter,
                step_type=StepType.OBSERVATION,
                content=f"Tool result: {str(result)[:200]}...",
                tool_result=result,
                confidence=0.9,
            )

        except Exception as e:
            return ReActStep(
                step_number=self.step_counter,
                step_type=StepType.OBSERVATION,
                content=f"Error executing tool: {str(e)}",
                confidence=0.1,
                requires_revision=True,
            )

    def _update_context(self, observation: ReActStep):
        """Update context based on observation.

        Args:
            observation: The observation step
        """
        if observation.tool_result:
            # Store relevant results in context
            self.current_context[f"observation_{observation.step_number}"] = {
                "result": observation.tool_result,
                "confidence": observation.confidence,
            }

    async def _reflect_on_progress(self) -> ReActStep:
        """Reflect on progress made so far.

        Returns:
            Reflection step
        """
        self.step_counter += 1

        # Analyze progress
        total_steps = len(self.steps)
        thought_steps = sum(1 for s in self.steps if s.step_type == StepType.THOUGHT)
        action_steps = sum(1 for s in self.steps if s.step_type == StepType.ACTION)
        failed_steps = sum(1 for s in self.steps if s.requires_revision)

        # Determine if revision is needed
        requires_revision = (
            failed_steps > 2
            or (action_steps > 5 and not self.solution_found)
            or (
                thought_steps > action_steps * 3
            )  # Too much thinking, not enough action
        )

        reflection_content = (
            f"Progress check: {total_steps} steps taken, "
            f"{action_steps} actions performed. "
        )

        if requires_revision:
            reflection_content += (
                "Need to revise approach - not making sufficient progress."
            )
        else:
            reflection_content += "Making good progress, continuing current approach."

        return ReActStep(
            step_number=self.step_counter,
            step_type=StepType.REFLECTION,
            content=reflection_content,
            requires_revision=requires_revision,
            metadata={
                "total_steps": total_steps,
                "thought_steps": thought_steps,
                "action_steps": action_steps,
                "failed_steps": failed_steps,
            },
        )

    async def _generate_conclusion(self) -> ReActStep:
        """Generate final conclusion.

        Returns:
            Conclusion step
        """
        self.step_counter += 1

        # Synthesize all observations and thoughts
        key_observations = [
            step
            for step in self.steps
            if step.step_type == StepType.OBSERVATION and step.confidence > 0.7
        ]

        conclusion_content = "Based on the reasoning process: "
        if key_observations:
            conclusion_content += (
                f"Found {len(key_observations)} key pieces of information. "
            )

        conclusion_content += "The final answer is..."

        return ReActStep(
            step_number=self.step_counter,
            step_type=StepType.CONCLUSION,
            content=conclusion_content,
            confidence=0.85,
        )

    def _generate_summary(self) -> dict[str, Any]:
        """Generate summary of the ReAct process.

        Returns:
            Summary dictionary
        """
        step_distribution = {}
        for step in self.steps:
            step_type = step.step_type.value
            step_distribution[step_type] = step_distribution.get(step_type, 0) + 1

        tools_used = {}
        for step in self.steps:
            if step.tool_used:
                tools_used[step.tool_used] = tools_used.get(step.tool_used, 0) + 1

        return {
            "total_steps": len(self.steps),
            "solution_found": self.solution_found,
            "step_distribution": step_distribution,
            "tools_used": tools_used,
            "average_confidence": (
                sum(s.confidence for s in self.steps) / len(self.steps)
                if self.steps
                else 0
            ),
            "revisions_needed": sum(1 for s in self.steps if s.requires_revision),
            "final_confidence": self.steps[-1].confidence if self.steps else 0,
        }

    def get_solution(self) -> str | None:
        """Get the final solution if found.

        Returns:
            Solution string or None
        """
        conclusion_steps = [
            step for step in self.steps if step.step_type == StepType.CONCLUSION
        ]

        if conclusion_steps:
            return conclusion_steps[-1].content

        return None

    def get_reasoning_path(self) -> list[dict[str, Any]]:
        """Get the complete reasoning path.

        Returns:
            List of steps in simplified format
        """
        return [
            {
                "step": step.step_number,
                "type": step.step_type.value,
                "content": (
                    step.content[:100] + "..."
                    if len(step.content) > 100
                    else step.content
                ),
                "tool": step.tool_used,
                "confidence": step.confidence,
            }
            for step in self.steps
        ]

    def visualize_reasoning(self) -> str:
        """Generate text visualization of reasoning process.

        Returns:
            ASCII representation of reasoning flow
        """
        lines = ["ReAct Reasoning Process:"]
        lines.append("=" * 50)

        for step in self.steps:
            # Icons for different step types
            icons = {
                StepType.THOUGHT: "💭",
                StepType.ACTION: "⚡",
                StepType.OBSERVATION: "👁️",
                StepType.REFLECTION: "🔄",
                StepType.CONCLUSION: "✅",
            }

            icon = icons.get(step.step_type, "•")
            confidence_bar = "█" * int(step.confidence * 10)

            lines.append(
                f"{step.step_number:2d}. {icon} {step.step_type.value:12s} "
                f"[{confidence_bar:10s}] {step.content[:40]}..."
            )

            if step.tool_used:
                lines.append(f"    └─ Tool: {step.tool_used}")

            if step.requires_revision:
                lines.append("    ⚠️  Requires revision")

        return "\n".join(lines)

    def start_trace(self, prompt: str) -> ReasoningTrace:
        """Start a new reasoning trace.

        Args:
            prompt: The prompt to trace

        Returns:
            A new ReasoningTrace instance
        """
        trace = ReasoningTrace(prompt=prompt)
        trace.add_step(
            "react_initialization",
            {
                "prompt": prompt,
                "approach": "react",
                "available_tools": list(self.tools.keys()),
                "max_steps": self.max_steps,
            },
        )
        return trace

    def format_trace(self, trace: ReasoningTrace) -> str:
        """Format a trace for human consumption.

        Args:
            trace: The trace to format

        Returns:
            Formatted string representation
        """
        if not trace.steps:
            return "No reasoning steps recorded."

        lines = [f"[{self.name}] ReAct Pattern Reasoning:"]
        lines.append(f"\nProblem: {trace.prompt}")
        lines.append("\nReasoning Process:")

        for i, step in enumerate(trace.steps, 1):
            lines.append(f"{i}. {step.step_type}: {step.description}")

            # Add relevant data based on step type
            if step.step_type == "react_initialization":
                tools = step.data.get("available_tools", [])
                if tools:
                    lines.append(f"   - Available tools: {', '.join(tools)}")
            elif step.step_type.startswith("thought_"):
                lines.append(f"   - Content: {step.data.get('content', '')[:80]}...")
                lines.append(f"   - Confidence: {step.data.get('confidence', 0):.2f}")
            elif step.step_type.startswith("action_"):
                lines.append(f"   - Tool used: {step.data.get('tool_used', 'unknown')}")
                lines.append(f"   - Content: {step.data.get('content', '')[:80]}...")
            elif step.step_type.startswith("observation_"):
                lines.append(f"   - Result: {step.data.get('content', '')[:80]}...")
                lines.append(f"   - Confidence: {step.data.get('confidence', 0):.2f}")
            elif step.step_type == "reasoning_summary":
                lines.append(f"   - Total steps: {step.data.get('total_steps', 0)}")
                lines.append(
                    f"   - Solution found: {step.data.get('solution_found', False)}"
                )
                lines.append(
                    f"   - Average confidence: {step.data.get('average_confidence', 0):.2f}"
                )

        if trace.result:
            lines.append(f"\nResult: {trace.result}")

        return "\n".join(lines)
