"""Data Analyst specialized agent for AgentiCraft.

This agent specializes in analyzing data, finding patterns,
and generating insights. A simple implementation focused on
synthesis and analysis rather than complex data science.
"""

from typing import Any, Dict, List, Optional

from agenticraft.core import Agent


class DataAnalyst(Agent):
    """Agent specialized in data analysis and insight generation.
    
    This agent can:
    - Analyze structured and unstructured data
    - Identify patterns and trends
    - Generate insights and recommendations
    - Create data-driven summaries
    
    Args:
        name: Name for this analyst
        **kwargs: Additional arguments passed to Agent
    """
    
    def __init__(self, name: str = "DataAnalyst", **kwargs):
        # Specialized instructions for data analysis
        instructions = """You are a specialized data analyst. Your role is to:
1. Analyze data to find meaningful patterns
2. Identify trends and correlations
3. Generate actionable insights
4. Present findings clearly with supporting evidence
5. Make data-driven recommendations

When analyzing, be thorough and objective. Always support conclusions with data."""
        
        # Override any provided instructions
        kwargs["instructions"] = instructions
        
        # Initialize the agent
        super().__init__(name=name, **kwargs)
    
    async def analyze(
        self,
        data_description: str,
        data: Optional[Dict[str, Any]] = None,
        analysis_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform analysis on provided data.
        
        Args:
            data_description: Description of the data to analyze
            data: Actual data (if available)
            analysis_type: Type of analysis ("general", "trend", "comparison", "correlation")
            context: Additional context
            
        Returns:
            Analysis results with insights
        """
        # Build analysis prompt
        prompt = f"""Perform a {analysis_type} analysis on the following data:

Data Description: {data_description}

Please:
1. Identify key patterns and trends
2. Calculate relevant statistics if needed
3. Generate actionable insights
4. Highlight any anomalies or interesting findings
5. Provide recommendations based on the analysis"""
        
        # Add actual data if provided
        if data:
            prompt += f"\n\nData:\n{self._format_data(data)}"
        
        # Add context
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt += f"\n\nContext:\n{context_str}"
        
        # Execute analysis
        response = await self.arun(prompt, context=context)
        
        # Structure the response
        return {
            "analysis_type": analysis_type,
            "data_description": data_description,
            "findings": response.content,
            "insights": self._extract_insights(response.content),
            "recommendations": self._extract_recommendations(response.content),
            "reasoning": response.reasoning,
            "analyst": self.name
        }
    
    async def synthesize_findings(
        self,
        findings: List[Dict[str, Any]],
        focus: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synthesize multiple findings into coherent insights.
        
        Args:
            findings: List of findings to synthesize
            focus: Specific aspect to focus on
            context: Additional context
            
        Returns:
            Synthesized insights
        """
        # Format findings for synthesis
        findings_text = "\n\n".join([
            f"Finding {i+1} ({f.get('source', 'Unknown')}):\n{f.get('content', str(f))}"
            for i, f in enumerate(findings)
        ])
        
        prompt = f"""Synthesize the following findings into coherent insights:

{findings_text}

Please:
1. Identify common themes and patterns
2. Resolve any contradictions
3. Create a unified narrative
4. Highlight the most important insights
5. Draw overall conclusions"""
        
        if focus:
            prompt += f"\n\nFocus specifically on: {focus}"
        
        response = await self.arun(prompt, context=context)
        
        return {
            "synthesis": response.content,
            "key_themes": self._extract_themes(response.content),
            "conclusions": self._extract_conclusions(response.content),
            "num_findings": len(findings),
            "focus": focus,
            "reasoning": response.reasoning
        }
    
    async def generate_insights(
        self,
        topic: str,
        data_points: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate insights from data points.
        
        Args:
            topic: The topic being analyzed
            data_points: List of relevant data points
            context: Additional context
            
        Returns:
            List of insights
        """
        data_text = "\n".join([f"- {point}" for point in data_points])
        
        prompt = f"""Generate insights about {topic} based on these data points:

{data_text}

Provide 3-5 key insights that:
1. Are actionable and specific
2. Are supported by the data
3. Reveal non-obvious patterns
4. Have practical implications"""
        
        response = await self.arun(prompt, context=context)
        
        # Extract insights as a list
        insights = self._extract_insights(response.content)
        return insights if insights else [response.content]
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """Format data for analysis prompt."""
        if isinstance(data, dict):
            return "\n".join([f"{k}: {v}" for k, v in data.items()])
        elif isinstance(data, list):
            return "\n".join([f"- {item}" for item in data])
        else:
            return str(data)
    
    def _extract_insights(self, content: str) -> List[str]:
        """Extract insights from analysis content."""
        insights = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Look for insight indicators
            if any(indicator in line_lower for indicator in ['insight:', 'finding:', 'key point:', '•', '-']):
                # Clean and add the insight
                insight = line.strip().lstrip('•-').strip()
                if insight and len(insight) > 10:
                    insights.append(insight)
        
        return insights[:5]  # Return top 5 insights
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from analysis."""
        recommendations = []
        lines = content.split('\n')
        
        in_recommendations = False
        for line in lines:
            line_lower = line.lower()
            if 'recommend' in line_lower:
                in_recommendations = True
            elif in_recommendations and line.strip():
                if line.strip().startswith(('•', '-', '1', '2', '3')):
                    recommendations.append(line.strip().lstrip('•-123. ').strip())
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extract key themes from synthesis."""
        # Simple extraction - in real implementation would be more sophisticated
        themes = []
        if "theme" in content.lower():
            # Extract themes from content
            lines = content.split('\n')
            for line in lines:
                if "theme" in line.lower() and ":" in line:
                    theme = line.split(':', 1)[1].strip()
                    if theme:
                        themes.append(theme)
        
        return themes[:4]  # Return top 4 themes
    
    def _extract_conclusions(self, content: str) -> List[str]:
        """Extract conclusions from synthesis."""
        conclusions = []
        lines = content.split('\n')
        
        in_conclusions = False
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['conclusion', 'conclude', 'overall']):
                in_conclusions = True
            elif in_conclusions and line.strip():
                conclusions.append(line.strip())
                if len(conclusions) >= 2:
                    break
        
        return conclusions
    
    def __repr__(self) -> str:
        """String representation."""
        return f"DataAnalyst(name='{self.name}', model='{self.config.model}')"
