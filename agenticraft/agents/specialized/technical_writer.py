"""Technical Writer specialized agent for AgentiCraft.

This agent specializes in creating well-structured documentation,
reports, and technical content. Simplified extraction focused on
clear communication and professional formatting.
"""

from typing import Any, Dict, List, Optional, Union

from agenticraft.core import Agent


class TechnicalWriter(Agent):
    """Agent specialized in technical writing and documentation.
    
    This agent can:
    - Format research findings into professional reports
    - Create clear, structured documentation
    - Adapt tone and style for different audiences
    - Generate executive summaries
    - Ensure consistent formatting and clarity
    
    Args:
        name: Name for this writer
        **kwargs: Additional arguments passed to Agent
    """
    
    def __init__(self, name: str = "TechnicalWriter", **kwargs):
        # Specialized instructions for technical writing
        instructions = """You are a specialized technical writer. Your role is to:
1. Transform research and data into clear, professional documents
2. Structure information logically with appropriate sections
3. Write for the target audience (technical, executive, general)
4. Ensure clarity, conciseness, and accuracy
5. Use proper formatting, headings, and visual hierarchy

Focus on making complex information accessible and actionable."""
        
        # Override any provided instructions
        kwargs["instructions"] = instructions
        
        # Initialize the agent
        super().__init__(name=name, **kwargs)
    
    async def create_report(
        self,
        title: str,
        findings: Union[str, List[Dict[str, Any]]],
        report_type: str = "research",
        audience: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a professional report from findings.
        
        Args:
            title: Report title
            findings: Research findings or data to include
            report_type: Type of report ("research", "analysis", "executive", "technical")
            audience: Target audience ("general", "technical", "executive")
            context: Additional context
            
        Returns:
            Formatted report with sections
        """
        # Format findings if provided as list
        if isinstance(findings, list):
            findings_text = self._format_findings_list(findings)
        else:
            findings_text = findings
        
        # Build report creation prompt
        prompt = f"""Create a professional {report_type} report with the following details:

Title: {title}
Target Audience: {audience}
Report Type: {report_type}

Findings to include:
{findings_text}

Please structure the report with:
1. Executive Summary (2-3 paragraphs)
2. Introduction
3. Main Findings (organized by theme)
4. Analysis and Insights
5. Recommendations
6. Conclusion

Adapt the language and detail level for the {audience} audience."""
        
        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt += f"\n\nAdditional Context:\n{context_str}"
        
        # Generate report
        response = await self.arun(prompt, context=context)
        
        # Parse sections from response
        sections = self._parse_report_sections(response.content)
        
        return {
            "title": title,
            "type": report_type,
            "audience": audience,
            "full_report": response.content,
            "sections": sections,
            "executive_summary": sections.get("executive_summary", ""),
            "recommendations": sections.get("recommendations", []),
            "writer": self.name,
            "reasoning": response.reasoning
        }
    
    async def write_summary(
        self,
        content: str,
        max_length: int = 500,
        style: str = "professional",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Write a concise summary of content.
        
        Args:
            content: Content to summarize
            max_length: Maximum length in words
            style: Writing style ("professional", "casual", "technical")
            context: Additional context
            
        Returns:
            Formatted summary
        """
        prompt = f"""Write a {style} summary of the following content in approximately {max_length} words:

{content}

Ensure the summary:
1. Captures all key points
2. Is self-contained and clear
3. Uses {style} tone
4. Stays within the word limit"""
        
        response = await self.arun(prompt, context=context)
        return response.content
    
    async def format_documentation(
        self,
        raw_content: str,
        doc_type: str = "technical",
        sections: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format raw content into structured documentation.
        
        Args:
            raw_content: Raw content to format
            doc_type: Type of documentation ("technical", "user", "api", "guide")
            sections: Optional list of sections to include
            context: Additional context
            
        Returns:
            Formatted documentation
        """
        sections_guide = ""
        if sections:
            sections_guide = "\n".join([f"- {section}" for section in sections])
            sections_text = f"\n\nInclude these sections:\n{sections_guide}"
        else:
            sections_text = ""
        
        prompt = f"""Format the following content into professional {doc_type} documentation:

{raw_content}

Create well-structured documentation with:
1. Clear headings and subheadings
2. Logical flow and organization
3. Code examples where appropriate
4. Bullet points for clarity
5. Consistent formatting{sections_text}

Target audience: {doc_type} documentation readers"""
        
        response = await self.arun(prompt, context=context)
        
        return {
            "type": doc_type,
            "formatted": response.content,
            "sections": self._extract_sections(response.content),
            "has_examples": "```" in response.content,
            "writer": self.name
        }
    
    async def create_executive_summary(
        self,
        report_content: str,
        key_findings: List[str],
        recommendations: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create an executive summary for C-level audience.
        
        Args:
            report_content: Full report content
            key_findings: List of key findings
            recommendations: List of recommendations
            context: Additional context
            
        Returns:
            Executive summary
        """
        findings_text = "\n".join([f"• {finding}" for finding in key_findings])
        recommendations_text = "\n".join([f"• {rec}" for rec in recommendations])
        
        prompt = f"""Create a compelling executive summary for C-level executives:

Key Findings:
{findings_text}

Recommendations:
{recommendations_text}

Context from full report:
{report_content[:500]}...

The executive summary should:
1. Start with the bottom line
2. Highlight business impact
3. Be scannable (use bullet points)
4. Focus on decisions and actions
5. Be no more than 2-3 paragraphs"""
        
        response = await self.arun(prompt, context=context)
        return response.content
    
    def _format_findings_list(self, findings: List[Dict[str, Any]]) -> str:
        """Format a list of findings for report creation."""
        formatted = []
        for i, finding in enumerate(findings, 1):
            source = finding.get("source", finding.get("agent", "Unknown"))
            content = finding.get("content", finding.get("findings", str(finding)))
            formatted.append(f"\n--- Finding {i} (Source: {source}) ---\n{content}")
        
        return "\n".join(formatted)
    
    def _parse_report_sections(self, content: str) -> Dict[str, Any]:
        """Parse report content into sections."""
        sections = {}
        current_section = None
        section_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if this is a section header
            if self._is_section_header(line):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(section_content).strip()
                
                # Start new section
                current_section = self._normalize_section_name(line)
                section_content = []
            else:
                section_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(section_content).strip()
        
        # Extract recommendations as list
        if "recommendations" in sections:
            sections["recommendations"] = self._extract_list_items(sections["recommendations"])
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is a section header."""
        line = line.strip()
        # Common patterns for headers
        return (
            line.startswith('#') or  # Markdown headers
            (line.endswith(':') and len(line) < 50) or  # Short lines ending with colon
            (line.isupper() and len(line) < 50) or  # ALL CAPS headers
            any(line.lower().startswith(header) for header in [
                'executive summary', 'introduction', 'findings',
                'analysis', 'recommendations', 'conclusion'
            ])
        )
    
    def _normalize_section_name(self, header: str) -> str:
        """Normalize section header to key name."""
        header = header.strip().lower()
        # Remove markdown symbols, colons, etc.
        header = header.lstrip('#').rstrip(':').strip()
        # Replace spaces with underscores
        header = header.replace(' ', '_')
        return header
    
    def _extract_sections(self, content: str) -> List[str]:
        """Extract section names from documentation."""
        sections = []
        for line in content.split('\n'):
            if self._is_section_header(line):
                sections.append(self._normalize_section_name(line))
        return sections
    
    def _extract_list_items(self, content: str) -> List[str]:
        """Extract bullet points or numbered items from content."""
        items = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Check for bullet points or numbered items
            if line.startswith(('•', '-', '*', '1', '2', '3', '4', '5')):
                item = line.lstrip('•-*12345. ').strip()
                if item:
                    items.append(item)
        
        return items
    
    def __repr__(self) -> str:
        """String representation."""
        return f"TechnicalWriter(name='{self.name}')"
