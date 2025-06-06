# Real-World Applications

See how AgentiCraft powers production applications across industries.

## Customer Support Bot {#customer-support}

Build an intelligent support agent that handles customer inquiries with context awareness and provider optimization.

```python
from agenticraft import Agent, ReasoningAgent, tool
import json

class CustomerSupportBot:
    def __init__(self):
        # Main conversational agent
        self.chat_agent = Agent(
            name="SupportChat",
            model="gpt-3.5-turbo",  # Cost-effective for simple queries
            memory_enabled=True,
            system_prompt="""You are a helpful customer support agent. 
            Be friendly, professional, and solution-oriented."""
        )
        
        # Reasoning agent for complex issues
        self.reasoning_agent = ReasoningAgent(
            name="IssueAnalyzer",
            model="gpt-4",  # More powerful for complex problems
            reasoning_style="chain_of_thought"
        )
        
        # Knowledge base tool
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search the company knowledge base."""
            # Simulate KB search
            kb = {
                "refund": "Refunds are processed within 5-7 business days...",
                "shipping": "Standard shipping takes 3-5 days...",
                "warranty": "All products come with a 1-year warranty..."
            }
            results = []
            for key, value in kb.items():
                if key in query.lower():
                    results.append(value)
            return "\n".join(results) if results else "No relevant articles found."
        
        # Ticket creation tool
        @tool
        def create_ticket(issue: str, priority: str = "normal") -> str:
            """Create a support ticket for complex issues."""
            ticket = {
                "id": f"TICK-{hash(issue) % 10000}",
                "issue": issue,
                "priority": priority,
                "status": "open"
            }
            return f"Created ticket {ticket['id']} with {priority} priority"
        
        self.chat_agent.tools = [search_knowledge_base, create_ticket]
    
    def handle_inquiry(self, customer_message: str) -> dict:
        """Handle a customer inquiry with intelligent routing."""
        
        # First, try simple response
        initial_response = self.chat_agent.run(customer_message)
        
        # Check if we need deeper analysis
        if any(word in customer_message.lower() 
               for word in ["complex", "multiple", "urgent", "legal", "technical"]):
            
            # Switch to reasoning agent for analysis
            analysis = self.reasoning_agent.run(
                f"Analyze this customer issue: {customer_message}"
            )
            
            # If high complexity, create ticket
            if analysis.confidence < 0.7 or "escalate" in analysis.content:
                ticket_result = self.chat_agent.run(
                    f"Create a ticket for: {customer_message}"
                )
                return {
                    "response": initial_response.content,
                    "ticket": ticket_result.content,
                    "analysis": analysis.reasoning
                }
        
        return {
            "response": initial_response.content,
            "ticket": None,
            "analysis": None
        }

# Usage
support_bot = CustomerSupportBot()

# Handle various inquiries
inquiries = [
    "How do I return a product?",
    "I have multiple technical issues with my device and need urgent help",
    "What's your refund policy?"
]

for inquiry in inquiries:
    print(f"\nCustomer: {inquiry}")
    result = support_bot.handle_inquiry(inquiry)
    print(f"Bot: {result['response']}")
    if result['ticket']:
        print(f"Action: {result['ticket']}")
```

## Data Analysis Pipeline {#data-analysis}

Process and analyze data using workflow agents with intelligent provider selection.

```python
from agenticraft import WorkflowAgent, Step
import pandas as pd

class DataAnalysisPipeline:
    def __init__(self):
        # Use efficient model for data processing
        self.processor = WorkflowAgent(
            name="DataProcessor",
            provider="ollama",
            model="llama2"
        )
        
        # Use powerful model for insights
        self.analyzer = WorkflowAgent(
            name="DataAnalyzer",
            provider="anthropic",
            model="claude-3-opus-20240229"
        )
    
    def analyze_sales_data(self, data_path: str):
        """Complete sales data analysis pipeline."""
        
        # Data processing workflow
        processing_workflow = [
            Step("load", "Load data from CSV"),
            Step("clean", "Clean and validate data"),
            Step("transform", "Calculate metrics and aggregations"),
            Step("prepare", "Prepare data for analysis")
        ]
        
        # Run processing with efficient model
        processed = self.processor.run_workflow(
            f"Process sales data from {data_path}",
            workflow=processing_workflow
        )
        
        # Analysis workflow with powerful model
        analysis_workflow = [
            Step("trends", "Identify sales trends"),
            Step("anomalies", "Detect anomalies"),
            Step("segments", "Analyze customer segments"),
            Step("forecast", "Generate forecast"),
            Step("insights", "Extract actionable insights"),
            Step("report", "Create executive summary")
        ]
        
        # Run deep analysis
        results = self.analyzer.run_workflow(
            f"Analyze processed sales data: {processed.steps['prepare'].output}",
            workflow=analysis_workflow
        )
        
        return {
            "processing": processed,
            "analysis": results,
            "executive_summary": results.steps["report"].output
        }

# Usage
pipeline = DataAnalysisPipeline()
results = pipeline.analyze_sales_data("sales_2024_q4.csv")
print(results["executive_summary"])
```

## Content Generator {#content-generator}

Create high-quality content with source citations and fact-checking.

```python
from agenticraft import ReasoningAgent, Agent, tool
import requests

class ContentGenerator:
    def __init__(self):
        # Research agent
        self.researcher = Agent(
            name="Researcher",
            model="gpt-4",
            system_prompt="You are a thorough researcher. Always cite sources."
        )
        
        # Writer with reasoning
        self.writer = ReasoningAgent(
            name="Writer",
            model="claude-3-opus-20240229",
            reasoning_style="chain_of_thought"
        )
        
        # Fact checker
        self.fact_checker = Agent(
            name="FactChecker",
            model="gpt-4",
            system_prompt="You verify facts and check sources. Be skeptical."
        )
        
        # Web search tool
        @tool
        def web_search(query: str) -> str:
            """Search the web for information."""
            # Simulate web search
            return f"Search results for: {query}\n1. Result 1...\n2. Result 2..."
        
        # Citation formatter
        @tool
        def format_citation(source: str, style: str = "APA") -> str:
            """Format a citation in the specified style."""
            return f"[{source}] - {style} formatted"
        
        self.researcher.tools = [web_search, format_citation]
    
    def generate_article(self, topic: str, word_count: int = 1000):
        """Generate a well-researched article."""
        
        # Phase 1: Research
        research_prompt = f"""
        Research the topic: {topic}
        Find credible sources and key information.
        Focus on recent developments and expert opinions.
        """
        research_results = self.researcher.run(research_prompt)
        
        # Phase 2: Writing with reasoning
        writing_prompt = f"""
        Write a {word_count}-word article about: {topic}
        
        Research findings:
        {research_results.content}
        
        Requirements:
        - Engaging introduction
        - Clear structure with sections
        - Evidence-based arguments
        - Compelling conclusion
        - Include citations
        """
        
        article = self.writer.run(writing_prompt)
        
        # Phase 3: Fact checking
        fact_check_prompt = f"""
        Fact-check this article:
        {article.content}
        
        Verify:
        - Accuracy of claims
        - Source reliability
        - Data correctness
        - Logical consistency
        """
        
        fact_check = self.fact_checker.run(fact_check_prompt)
        
        # Phase 4: Final revision if needed
        if "inaccurate" in fact_check.content.lower():
            revision_prompt = f"""
            Revise the article based on fact-checking feedback:
            {fact_check.content}
            
            Original article:
            {article.content}
            """
            article = self.writer.run(revision_prompt)
        
        return {
            "article": article.content,
            "reasoning": article.reasoning,
            "research": research_results.content,
            "fact_check": fact_check.content,
            "confidence": article.confidence
        }

# Usage
generator = ContentGenerator()
result = generator.generate_article(
    topic="The Future of Renewable Energy",
    word_count=1500
)

print("ARTICLE:")
print(result["article"])
print(f"\nConfidence: {result['confidence']:.2%}")
```

## Multi-Language Customer Service

Support customers in multiple languages with automatic translation and cultural adaptation.

```python
from agenticraft import Agent, tool

class MultilingualSupport:
    def __init__(self):
        self.agents = {}
        
        # Create specialized agents for different languages
        languages = {
            "en": ("gpt-4", "You are a helpful English-speaking support agent."),
            "es": ("gpt-4", "Eres un agente de soporte útil que habla español."),
            "fr": ("gpt-4", "Vous êtes un agent de support utile qui parle français."),
            "de": ("gpt-4", "Sie sind ein hilfreicher deutschsprachiger Support-Agent."),
            "zh": ("gpt-4", "您是一位乐于助人的中文客服代表。")
        }
        
        for lang, (model, prompt) in languages.items():
            self.agents[lang] = Agent(
                name=f"Support_{lang}",
                model=model,
                system_prompt=prompt,
                memory_enabled=True
            )
        
        # Language detection tool
        @tool
        def detect_language(text: str) -> str:
            """Detect the language of the text."""
            # Simple detection (in production, use a proper library)
            if any(word in text.lower() for word in ["hello", "help", "please"]):
                return "en"
            elif any(word in text.lower() for word in ["hola", "ayuda", "por favor"]):
                return "es"
            elif any(word in text.lower() for word in ["bonjour", "aide", "merci"]):
                return "fr"
            elif any(word in text.lower() for word in ["hallo", "hilfe", "bitte"]):
                return "de"
            elif any(char in text for char in "你好帮助请"):
                return "zh"
            return "en"  # Default
        
        # Cultural adaptation tool
        @tool
        def adapt_culturally(response: str, culture: str) -> str:
            """Adapt response for cultural appropriateness."""
            adaptations = {
                "formal": "Please use formal language and titles.",
                "casual": "Keep it friendly and casual.",
                "direct": "Be direct and to the point.",
                "indirect": "Be polite and indirect."
            }
            return f"{response} [{adaptations.get(culture, 'Standard')}]"
        
        # Add tools to all agents
        for agent in self.agents.values():
            agent.tools = [detect_language, adapt_culturally]
    
    def handle_query(self, message: str, user_id: str = None):
        """Handle a query in any supported language."""
        
        # Detect language
        lang = self.agents["en"].run(f"Detect language: {message}").content
        
        # Select appropriate agent
        agent = self.agents.get(lang, self.agents["en"])
        
        # Generate response
        response = agent.run(message)
        
        # Cultural adaptation based on language
        cultural_styles = {
            "en": "casual",
            "es": "casual",
            "fr": "formal",
            "de": "direct",
            "zh": "formal"
        }
        
        adapted_response = agent.run(
            f"Adapt culturally for {cultural_styles.get(lang, 'casual')}: {response.content}"
        )
        
        return {
            "language": lang,
            "response": adapted_response.content,
            "original": response.content
        }

# Usage
support = MultilingualSupport()

queries = [
    "Hello, I need help with my order",
    "Hola, necesito ayuda con mi pedido",
    "Bonjour, j'ai besoin d'aide avec ma commande",
    "你好，我需要订单帮助"
]

for query in queries:
    result = support.handle_query(query)
    print(f"\nQuery: {query}")
    print(f"Language: {result['language']}")
    print(f"Response: {result['response']}")
```

## Best Practices from Production

1. **Provider Optimization**
   - Use GPT-3.5-Turbo for simple queries
   - Switch to GPT-4 for complex reasoning
   - Use Claude for long documents
   - Deploy Ollama for sensitive data

2. **Error Handling**
   ```python
   try:
       response = agent.run(prompt)
   except ProviderError:
       # Fallback to alternative provider
       agent.set_provider("ollama", model="llama2")
       response = agent.run(prompt)
   ```

3. **Cost Management**
   - Track token usage per request
   - Set budget limits
   - Use caching for repeated queries
   - Batch similar requests

4. **Performance**
   - Enable parallel processing for workflows
   - Cache tool results
   - Use connection pooling
   - Implement request queuing

5. **Monitoring**
   - Log all interactions
   - Track response times
   - Monitor error rates
   - Set up alerts for anomalies

## Next Steps

- [Explore more examples](index.md)
- [Learn about performance tuning](../guides/performance-tuning.md)
- [Read the API reference](../reference/index.md)
