"""ReasoningAgent implementation for AgentiCraft.

The ReasoningAgent provides transparent reasoning capabilities, exposing
its thought process step-by-step. This is ideal for educational purposes,
debugging, and building trust through transparency.
"""

from typing import Any, Dict, List, Optional, Union
import json

from pydantic import BaseModel, Field

from ..core.agent import Agent, AgentResponse
from ..core.reasoning import ChainOfThought, ReasoningTrace, ReasoningStep
from ..core.types import Message, MessageRole


class ReasoningAgent(Agent):
    """An agent that exposes its reasoning process transparently.
    
    ReasoningAgent extends the base Agent class to provide detailed
    visibility into the reasoning process. It uses Chain of Thought
    by default and formats responses to include step-by-step thinking.
    
    Example:
        Basic usage::
        
            agent = ReasoningAgent(
                name="Tutor",
                instructions="You are a helpful tutor who explains step-by-step."
            )
            
            response = await agent.think_and_act("How do I solve 2x + 5 = 13?")
            
            print("Answer:", response.content)
            print("\nReasoning Process:")
            print(response.reasoning)
            
            # Access detailed reasoning
            for step in response.reasoning_steps:
                print(f"{step.number}. {step.description}")
                if step.conclusion:
                    print(f"   Conclusion: {step.conclusion}")
    """
    
    def __init__(
        self,
        name: str = "ReasoningAgent",
        instructions: str = "You are a helpful assistant that explains your reasoning step-by-step.",
        **kwargs
    ):
        """Initialize ReasoningAgent.
        
        Args:
            name: Agent name
            instructions: System instructions (augmented with reasoning prompt)
            **kwargs: Additional configuration passed to base Agent
        """
        # Augment instructions to encourage step-by-step reasoning
        reasoning_instructions = (
            f"{instructions}\n\n"
            "IMPORTANT: Always explain your reasoning process step-by-step. "
            "For each step:\n"
            "1. State what you're doing\n"
            "2. Explain why\n"
            "3. Show any calculations or logic\n"
            "4. State your conclusion for that step\n\n"
            "Format your response with clear sections:\n"
            "- REASONING: Your step-by-step thought process\n"
            "- ANSWER: Your final answer\n"
        )
        
        # Use Chain of Thought reasoning by default
        if 'reasoning_pattern' not in kwargs:
            kwargs['reasoning_pattern'] = ChainOfThought()
            
        super().__init__(
            name=name,
            instructions=reasoning_instructions,
            **kwargs
        )
        
        self.reasoning_history: List[ReasoningTrace] = []
    
    async def think_and_act(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        expose_thinking: bool = True,
        **kwargs
    ) -> 'ReasoningResponse':
        """Think through a problem step-by-step and act on it.
        
        Args:
            prompt: The problem or question to solve
            context: Optional context
            expose_thinking: Whether to expose internal reasoning
            **kwargs: Additional arguments passed to LLM
            
        Returns:
            ReasoningResponse with detailed reasoning information
        """
        # Start reasoning trace
        trace = self._reasoning.start_trace(prompt)
        
        # Add thinking step
        trace.add_step("thinking", {
            "approach": "step_by_step",
            "expose_thinking": expose_thinking
        })
        
        # If expose_thinking, add a special prompt
        thinking_prompt = prompt
        if expose_thinking:
            thinking_prompt = (
                f"Please think through this step-by-step, showing all your reasoning:\n\n"
                f"{prompt}\n\n"
                f"Remember to clearly separate your REASONING from your final ANSWER."
            )
        
        # Run the agent with thinking prompt
        response = await self.arun(thinking_prompt, context, **kwargs)
        
        # Parse the response to extract reasoning steps
        reasoning_steps = self._parse_reasoning_steps(response.content, trace)
        
        # Store reasoning trace
        self.reasoning_history.append(trace)
        
        # Create enhanced response
        return ReasoningResponse(
            content=response.content,
            reasoning=response.reasoning,
            reasoning_steps=reasoning_steps,
            reasoning_trace=trace,
            tool_calls=response.tool_calls,
            metadata=response.metadata,
            agent_id=response.agent_id
        )
    
    def _parse_reasoning_steps(
        self, 
        content: str, 
        trace: ReasoningTrace
    ) -> List['ReasoningStepDetail']:
        """Parse reasoning steps from the response content.
        
        Args:
            content: The response content
            trace: The reasoning trace
            
        Returns:
            List of detailed reasoning steps
        """
        steps = []
        
        # Try to extract structured reasoning
        lines = content.split('\n')
        current_step = None
        step_number = 0
        in_reasoning_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check for reasoning section
            if line.upper().startswith('REASONING:'):
                in_reasoning_section = True
                continue
            elif line.upper().startswith('ANSWER:'):
                in_reasoning_section = False
                continue
                
            if in_reasoning_section and line:
                # Look for numbered steps
                if (line[0].isdigit() and '.' in line) or line.startswith('Step'):
                    if current_step:
                        steps.append(current_step)
                    
                    step_number += 1
                    # Extract step description
                    desc_start = line.find('.') + 1 if '.' in line else line.find(':') + 1
                    description = line[desc_start:].strip()
                    
                    current_step = ReasoningStepDetail(
                        number=step_number,
                        description=description,
                        details=[],
                        conclusion=None
                    )
                elif current_step and line.startswith(('-', '•', '*')):
                    # Add as detail to current step
                    current_step.details.append(line[1:].strip())
                elif current_step and ('therefore' in line.lower() or 
                                     'conclusion:' in line.lower() or
                                     'so,' in line.lower()):
                    # This is a conclusion
                    current_step.conclusion = line
        
        # Add the last step
        if current_step:
            steps.append(current_step)
        
        # If no structured steps found, create from trace
        if not steps and trace.steps:
            for i, trace_step in enumerate(trace.steps):
                if trace_step.step_type not in ['analyzing_prompt', 'breakdown']:
                    steps.append(ReasoningStepDetail(
                        number=i + 1,
                        description=trace_step.description,
                        details=[f"{k}: {v}" for k, v in trace_step.data.items()],
                        conclusion=None
                    ))
        
        return steps
    
    async def analyze(
        self,
        prompt: str,
        perspectives: List[str] = None,
        **kwargs
    ) -> 'AnalysisResponse':
        """Analyze a topic from multiple perspectives.
        
        Args:
            prompt: The topic or question to analyze
            perspectives: List of perspectives to consider
            **kwargs: Additional arguments
            
        Returns:
            AnalysisResponse with multi-perspective analysis
        """
        if perspectives is None:
            perspectives = ["practical", "theoretical", "ethical", "economic"]
        
        # Build analysis prompt
        analysis_prompt = (
            f"Please analyze the following from multiple perspectives:\n\n"
            f"{prompt}\n\n"
            f"Consider these perspectives:\n"
        )
        for perspective in perspectives:
            analysis_prompt += f"- {perspective.capitalize()} perspective\n"
        
        analysis_prompt += "\nProvide a thorough analysis for each perspective."
        
        # Get analysis
        response = await self.think_and_act(analysis_prompt, **kwargs)
        
        # Parse perspectives from response
        perspective_analyses = self._parse_perspectives(response.content, perspectives)
        
        return AnalysisResponse(
            content=response.content,
            perspectives=perspective_analyses,
            reasoning_steps=response.reasoning_steps,
            synthesis=self._synthesize_perspectives(perspective_analyses),
            metadata=response.metadata
        )
    
    def _parse_perspectives(
        self, 
        content: str, 
        perspectives: List[str]
    ) -> Dict[str, str]:
        """Parse perspective analyses from content."""
        analyses = {}
        lines = content.split('\n')
        current_perspective = None
        current_content = []
        
        for line in lines:
            # Check if this line starts a new perspective
            for perspective in perspectives:
                if perspective.lower() in line.lower() and 'perspective' in line.lower():
                    if current_perspective:
                        analyses[current_perspective] = '\n'.join(current_content).strip()
                    current_perspective = perspective
                    current_content = []
                    break
            else:
                if current_perspective:
                    current_content.append(line)
        
        # Add the last perspective
        if current_perspective:
            analyses[current_perspective] = '\n'.join(current_content).strip()
        
        return analyses
    
    def _synthesize_perspectives(self, perspectives: Dict[str, str]) -> str:
        """Create a synthesis of multiple perspectives."""
        if not perspectives:
            return "No perspectives to synthesize."
        
        synthesis = "Synthesis: Considering all perspectives, "
        
        # Simple synthesis based on perspective count
        if len(perspectives) > 1:
            synthesis += "this topic reveals multiple important dimensions. "
            synthesis += f"The {', '.join(perspectives.keys())} perspectives "
            synthesis += "each contribute valuable insights that should be balanced."
        else:
            key = list(perspectives.keys())[0]
            synthesis += f"the {key} perspective provides the primary framework for understanding."
        
        return synthesis
    
    def get_reasoning_history(self, limit: int = 10) -> List[ReasoningTrace]:
        """Get recent reasoning history.
        
        Args:
            limit: Maximum number of traces to return
            
        Returns:
            List of recent reasoning traces
        """
        return self.reasoning_history[-limit:]
    
    def explain_last_response(self) -> str:
        """Explain the reasoning behind the last response."""
        if not self.reasoning_history:
            return "No reasoning history available."
        
        last_trace = self.reasoning_history[-1]
        return self._reasoning.format_trace(last_trace)


class ReasoningStepDetail(BaseModel):
    """Detailed information about a reasoning step."""
    
    number: int
    description: str
    details: List[str] = Field(default_factory=list)
    conclusion: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    def __str__(self) -> str:
        """String representation of the step."""
        s = f"Step {self.number}: {self.description}"
        if self.details:
            s += f" (Details: {len(self.details)})"
        if self.conclusion:
            s += f" → {self.conclusion}"
        return s


class ReasoningResponse(AgentResponse):
    """Enhanced response with detailed reasoning information."""
    
    reasoning_steps: List[ReasoningStepDetail] = Field(default_factory=list)
    reasoning_trace: Optional[ReasoningTrace] = None
    
    @property
    def step_count(self) -> int:
        """Get the number of reasoning steps."""
        return len(self.reasoning_steps)
    
    def get_step(self, number: int) -> Optional[ReasoningStepDetail]:
        """Get a specific reasoning step by number."""
        for step in self.reasoning_steps:
            if step.number == number:
                return step
        return None
    
    def format_reasoning(self) -> str:
        """Format reasoning steps as readable text."""
        if not self.reasoning_steps:
            return "No detailed reasoning steps available."
        
        lines = ["Reasoning Process:"]
        for step in self.reasoning_steps:
            lines.append(f"\n{step.number}. {step.description}")
            for detail in step.details:
                lines.append(f"   - {detail}")
            if step.conclusion:
                lines.append(f"   → {step.conclusion}")
        
        return '\n'.join(lines)


class AnalysisResponse(ReasoningResponse):
    """Response from multi-perspective analysis."""
    
    perspectives: Dict[str, str] = Field(default_factory=dict)
    synthesis: str = ""
    
    def get_perspective(self, name: str) -> Optional[str]:
        """Get analysis for a specific perspective."""
        return self.perspectives.get(name)
    
    def format_analysis(self) -> str:
        """Format the complete analysis."""
        lines = ["Multi-Perspective Analysis:"]
        
        for perspective, analysis in self.perspectives.items():
            lines.append(f"\n{perspective.upper()} PERSPECTIVE:")
            lines.append(analysis)
        
        if self.synthesis:
            lines.append(f"\n{self.synthesis}")
        
        return '\n'.join(lines)
