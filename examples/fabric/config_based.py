"""
Example: Configuration-Based Agents

This example shows how to use agenticraft.yaml to configure agents.
"""

import asyncio
from pathlib import Path

from agenticraft.fabric import from_config, agent, chain, parallel

# Load configuration from yaml file
CONFIG_FILE = Path(__file__).parent / "agenticraft.yaml"


@from_config(CONFIG_FILE)
class ResearchTeam:
    """
    A team of agents configured via YAML.
    
    Each agent's configuration (servers, model, temperature, etc.)
    is loaded from the agenticraft.yaml file.
    """
    
    @agent("researcher")
    async def research(self, topic: str) -> Dict[str, Any]:
        """Research agent - configuration from YAML."""
        print(f"🔍 Researcher investigating: {topic}")
        
        # Search across multiple MCP servers (as configured)
        results = {}
        
        # Web search
        web_results = await self.tools.web_search(query=topic)
        results['web'] = web_results
        
        # Academic search (if arxiv MCP is configured)
        try:
            papers = await self.tools.search_papers(
                query=topic,
                max_results=5
            )
            results['academic'] = papers
        except AttributeError:
            print("  ℹ️  Academic search not available")
        
        return results
    
    @agent("analyst")  
    async def analyze(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyst agent with reasoning enabled.
        
        Uses chain_of_thought reasoning as configured in YAML.
        """
        print("🧠 Analyst processing research data...")
        
        # The reasoning pattern is automatically applied
        # due to YAML configuration
        
        analysis = await self.tools.analyze_data(
            data=research_data,
            output_format="structured"
        )
        
        insights = await self.tools.extract_insights(
            analysis=analysis
        )
        
        return {
            'analysis': analysis,
            'insights': insights,
            'confidence': 0.85
        }
    
    @agent("writer")
    async def write(self, analysis: Dict[str, Any]) -> str:
        """
        Writer agent using Claude (as configured).
        
        Only uses specific tools as listed in YAML config.
        """
        print("✍️  Writer creating content...")
        
        # These tools are specifically configured in YAML
        outline = await self.tools.generate_outline(
            insights=analysis['insights']
        )
        
        sections = []
        for section in outline['sections']:
            content = await self.tools.write_section(
                section=section,
                context=analysis
            )
            sections.append(content)
        
        # Edit and polish
        final_content = await self.tools.edit_content(
            sections=sections,
            style="professional"
        )
        
        return final_content
    
    @agent("coordinator")
    async def coordinate(self, task: str) -> Dict[str, Any]:
        """
        Coordinator using multiple protocols.
        
        This agent can:
        - Use MCP tools
        - Communicate with A2A agents  
        - Discover via ANP
        """
        print(f"🎯 Coordinator handling: {task}")
        
        # Discover available agents via ANP
        try:
            available_agents = await self.tools.discover_agents(
                capability="research"
            )
            print(f"  Found {len(available_agents)} research agents")
        except:
            available_agents = []
        
        # Delegate to A2A agents if available
        if available_agents:
            # Use A2A protocol for delegation
            delegated_result = await self.tools.delegate_task(
                agent_id=available_agents[0]['id'],
                task=task
            )
            return {'delegated': True, 'result': delegated_result}
        
        # Otherwise use local MCP tools
        return {
            'delegated': False,
            'result': await self.tools.execute_locally(task=task)
        }


# Example of chaining configured agents
class ResearchPipeline:
    """Pipeline using the configured agents."""
    
    def __init__(self):
        self.team = ResearchTeam()
    
    async def full_research_pipeline(self, topic: str) -> str:
        """
        Complete research pipeline:
        1. Research the topic
        2. Analyze findings  
        3. Write report
        """
        print(f"\n🚀 Starting research pipeline for: {topic}")
        print("=" * 50)
        
        # Step 1: Research
        research_data = await self.team.research(topic)
        print(f"✅ Research complete: {len(research_data)} sources")
        
        # Step 2: Analyze
        analysis = await self.team.analyze(research_data)
        print(f"✅ Analysis complete: {len(analysis['insights'])} insights")
        
        # Step 3: Write
        report = await self.team.write(analysis)
        print(f"✅ Report complete: {len(report)} characters")
        
        return report
    
    async def parallel_research(self, topics: List[str]) -> List[Dict]:
        """
        Research multiple topics in parallel.
        
        Demonstrates parallel execution of configured agents.
        """
        print(f"\n🔀 Researching {len(topics)} topics in parallel")
        
        # Create tasks for parallel execution
        tasks = [
            self.team.research(topic) 
            for topic in topics
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks)
        
        # Analyze all results together
        combined_analysis = await self.team.analyze({
            'topics': topics,
            'results': results
        })
        
        return combined_analysis


# Standalone function showing config override
@agent(
    "custom_researcher",
    servers=["http://localhost:3000/mcp"],  # Override servers
    model="gpt-3.5-turbo"  # Override model
)
async def custom_researcher(self, query: str):
    """
    Agent with custom configuration overriding YAML.
    
    Even when using @from_config, individual agents
    can override specific settings.
    """
    return await self.tools.quick_search(query=query)


async def main():
    """Demonstrate configuration-based agents."""
    
    print("📋 Configuration-Based Agents Example")
    print("=" * 60)
    
    # Check if config file exists
    if not CONFIG_FILE.exists():
        print(f"⚠️  Config file not found: {CONFIG_FILE}")
        print("Creating example configuration...")
        # Config file should already be created
        return
    
    print(f"✅ Loaded configuration from: {CONFIG_FILE}")
    
    # Create pipeline
    pipeline = ResearchPipeline()
    
    # Example 1: Full research pipeline
    try:
        print("\n=== Example 1: Full Research Pipeline ===")
        report = await pipeline.full_research_pipeline(
            "The impact of AI on software development"
        )
        print(f"\n📄 Final Report Preview:")
        print(report[:500] + "..." if len(report) > 500 else report)
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        print("Make sure MCP servers are running as configured in agenticraft.yaml")
    
    # Example 2: Parallel research
    try:
        print("\n=== Example 2: Parallel Research ===")
        topics = [
            "AI safety",
            "Quantum computing",
            "Blockchain technology"
        ]
        
        analysis = await pipeline.parallel_research(topics)
        print(f"\n📊 Parallel Analysis Complete:")
        print(f"  - Topics analyzed: {len(topics)}")
        print(f"  - Insights found: {len(analysis.get('insights', []))}")
        
    except Exception as e:
        print(f"❌ Parallel research failed: {e}")
    
    # Example 3: Custom configured agent
    try:
        print("\n=== Example 3: Custom Override ===")
        result = await custom_researcher("AgentiCraft features")
        print(f"Custom result: {result}")
        
    except Exception as e:
        print(f"❌ Custom agent failed: {e}")
    
    print("\n✅ Configuration examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
