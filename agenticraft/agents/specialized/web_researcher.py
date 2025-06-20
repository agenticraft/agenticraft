"""Web Researcher specialized agent for AgentiCraft.

This agent specializes in web research, information gathering,
and summarization. Simplified from Agentic Framework's version.
"""

from typing import Any, Dict, List, Optional

from agenticraft.core import Agent


class WebResearcher(Agent):
    """Agent specialized in web research and information gathering.
    
    This agent can:
    - Search the web for information
    - Extract and summarize content
    - Focus on relevant findings
    - Provide clear, researched responses
    
    Args:
        name: Name for this researcher
        **kwargs: Additional arguments passed to Agent
    """
    
    def __init__(self, name: str = "WebResearcher", **kwargs):
        # Specialized instructions for web research
        instructions = """You are a specialized web researcher. Your role is to:
1. Search for relevant information on the web
2. Extract key findings from search results
3. Summarize information clearly and accurately
4. Always cite your sources
5. Focus on factual, up-to-date information

When researching, be thorough but concise. Prioritize authoritative sources."""
        
        # Override any provided instructions with our specialized ones
        kwargs["instructions"] = instructions
        
        # Initialize the agent
        super().__init__(name=name, **kwargs)
    
    async def research(
        self,
        topic: str,
        max_results: int = 5,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Conduct focused research on a specific topic.
        
        Args:
            topic: The topic to research
            max_results: Maximum number of search results to process
            context: Additional context for the research
            
        Returns:
            Dictionary containing research findings and sources
        """
        # Build research prompt
        prompt = f"""Research the following topic thoroughly:

Topic: {topic}

Please:
1. Search for relevant information
2. Extract key findings from multiple sources
3. Synthesize the information
4. Provide a comprehensive summary

Focus on recent, authoritative sources."""
        
        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt += f"\n\nAdditional context:\n{context_str}"
        
        # Execute research
        response = await self.arun(prompt, context=context)
        
        # Structure the response
        return {
            "topic": topic,
            "findings": response.content,
            "reasoning": response.reasoning,
            "sources": self._extract_sources(response),
            "researcher": self.name
        }
    
    async def fact_check(
        self,
        claim: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fact-check a specific claim.
        
        Args:
            claim: The claim to verify
            context: Additional context
            
        Returns:
            Fact-checking results with sources
        """
        prompt = f"""Fact-check the following claim:

Claim: {claim}

Please:
1. Search for evidence supporting or refuting this claim
2. Check multiple authoritative sources
3. Provide a clear verdict: TRUE, FALSE, or PARTIALLY TRUE
4. Explain your reasoning with evidence"""
        
        response = await self.arun(prompt, context=context)
        
        return {
            "claim": claim,
            "verdict": self._extract_verdict(response.content),
            "evidence": response.content,
            "sources": self._extract_sources(response),
            "reasoning": response.reasoning
        }
    
    async def summarize_topic(
        self,
        topic: str,
        length: str = "medium",
        audience: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a summary of a topic for a specific audience.
        
        Args:
            topic: Topic to summarize
            length: "short", "medium", or "long"
            audience: Target audience (e.g., "general", "technical", "executive")
            context: Additional context
            
        Returns:
            Formatted summary
        """
        length_guides = {
            "short": "2-3 paragraphs",
            "medium": "4-5 paragraphs",
            "long": "comprehensive multi-section"
        }
        
        prompt = f"""Create a {length_guides.get(length, 'medium')} summary about:

Topic: {topic}
Target Audience: {audience}

Adjust the language and detail level for the specified audience.
Include key facts, recent developments, and important context."""
        
        response = await self.arun(prompt, context=context)
        return response.content
    
    def _extract_sources(self, response) -> List[str]:
        """Extract sources from response - simplified version."""
        # In a real implementation, this would parse citations more carefully
        sources = []
        if hasattr(response, 'tool_calls'):
            for call in response.tool_calls:
                if call.get('tool') == 'web_search':
                    # Extract URLs from search results
                    pass
        return sources
    
    def _extract_verdict(self, content: str) -> str:
        """Extract fact-check verdict from content."""
        content_lower = content.lower()
        if "true" in content_lower and "false" not in content_lower:
            return "TRUE"
        elif "false" in content_lower:
            return "FALSE"
        elif "partially true" in content_lower or "partly true" in content_lower:
            return "PARTIALLY TRUE"
        else:
            return "UNCLEAR"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"WebResearcher(name='{self.name}', model='{self.config.model}')"
