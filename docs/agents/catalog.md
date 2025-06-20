# AgentiCraft Agent Catalog

A comprehensive guide to all specialized agents available in AgentiCraft.

## 🤖 Overview

AgentiCraft provides 9 specialized agents, each designed for specific tasks and domains. These agents can work independently or be combined in multi-agent workflows.

## 📚 Core Research & Analysis Agents

### 1. WebResearcher 🔍
**Specialty:** Web research and information gathering

**Key Methods:**
- `research(topic)` - Comprehensive web research
- `summarize(content)` - Intelligent summarization
- `extract_facts(text)` - Fact extraction

**Best For:**
- Market research
- Competitive analysis
- Fact-checking
- Information synthesis

**Example:**
```python
from agenticraft.agents.specialized import WebResearcher

researcher = WebResearcher()
results = await researcher.research("AI frameworks comparison")
```

### 2. DataAnalyst 📊
**Specialty:** Data analysis and insights generation

**Key Methods:**
- `analyze(data)` - Statistical analysis
- `visualize(data, chart_type)` - Data visualization
- `find_patterns(data)` - Pattern recognition
- `generate_insights(analysis)` - Insight generation

**Best For:**
- Statistical analysis
- Trend identification
- Report generation
- Data-driven decisions

**Example:**
```python
from agenticraft.agents.specialized import DataAnalyst

analyst = DataAnalyst()
insights = await analyst.analyze(sales_data)
```

### 3. BusinessAnalyst 💼
**Specialty:** Requirements analysis and process optimization

**Key Methods:**
- `analyze_requirements(project_description, stakeholders)` - Requirements gathering
- `create_process_map(process_name, current_state)` - Process mapping
- `perform_gap_analysis(current_state, desired_state)` - Gap analysis
- `create_business_case(project_name, investment, benefits)` - Business case development

**Best For:**
- Requirements documentation
- Process improvement
- ROI analysis
- Stakeholder management

**Example:**
```python
from agenticraft.agents.specialized import BusinessAnalyst

ba = BusinessAnalyst()
requirements = await ba.analyze_requirements(
    "New customer portal",
    stakeholders=["Sales", "IT", "Customers"]
)
```

## 🛠️ Technical & Development Agents

### 4. CodeReviewer 👨‍💻
**Specialty:** Code review and quality assessment

**Key Methods:**
- `review_code(code, language)` - Comprehensive code review
- `check_security(code)` - Security vulnerability detection
- `suggest_improvements(code)` - Optimization suggestions
- `analyze_complexity(code)` - Complexity analysis

**Best For:**
- Pull request reviews
- Security audits
- Code quality improvement
- Best practices enforcement

**Example:**
```python
from agenticraft.agents.specialized import CodeReviewer

reviewer = CodeReviewer()
review = await reviewer.review_code(code_snippet, language="python")
```

### 5. DevOpsEngineer 🚀
**Specialty:** Deployment automation and infrastructure

**Key Methods:**
- `plan_deployment(service, version, environment, strategy)` - Deployment planning
- `generate_ci_cd_pipeline(project_type, platform)` - CI/CD configuration
- `create_kubernetes_manifest(service, image, replicas)` - K8s manifests
- `setup_monitoring(service, metrics)` - Monitoring setup

**Best For:**
- Automated deployments
- Infrastructure as Code
- CI/CD pipelines
- Container orchestration

**Example:**
```python
from agenticraft.agents.specialized import DevOpsEngineer

devops = DevOpsEngineer()
deployment_plan = await devops.plan_deployment(
    service="api-gateway",
    version="2.0.0",
    environment="production",
    strategy="canary"
)
```

### 6. QATester 🧪
**Specialty:** Quality assurance and testing

**Key Methods:**
- `create_test_plan(project_name, features, test_types)` - Test planning
- `generate_test_cases(feature_description, test_type)` - Test case generation
- `report_bug(title, description, steps, expected, actual)` - Bug reporting
- `perform_performance_test(endpoint, load_profile)` - Performance testing

**Best For:**
- Test automation
- Bug tracking
- Performance testing
- Quality metrics

**Example:**
```python
from agenticraft.agents.specialized import QATester

qa = QATester()
test_plan = await qa.create_test_plan(
    "E-commerce Platform",
    features=["Shopping Cart", "Checkout", "Payment"],
    test_types=["functional", "integration", "performance"]
)
```

## 📝 Content & Communication Agents

### 7. TechnicalWriter ✍️
**Specialty:** Documentation and technical content

**Key Methods:**
- `write_documentation(topic, audience)` - Documentation creation
- `create_tutorial(subject, level)` - Tutorial writing
- `generate_api_docs(api_spec)` - API documentation
- `improve_clarity(content)` - Content improvement

**Best For:**
- User documentation
- API documentation
- Technical tutorials
- Knowledge bases

**Example:**
```python
from agenticraft.agents.specialized import TechnicalWriter

writer = TechnicalWriter()
docs = await writer.write_documentation(
    topic="Authentication System",
    audience="developers"
)
```

### 8. SEOSpecialist 🔍
**Specialty:** Search engine optimization

**Key Methods:**
- `analyze_content(content, target_keywords)` - SEO analysis
- `suggest_keywords(topic, intent)` - Keyword research
- `optimize_meta_tags(title, description, keywords)` - Meta optimization
- `analyze_competitors(topic, competitors)` - Competitor analysis

**Best For:**
- Content optimization
- Keyword research
- SEO strategy
- Competitor analysis

**Example:**
```python
from agenticraft.agents.specialized import SEOSpecialist

seo = SEOSpecialist()
analysis = await seo.analyze_content(
    blog_post,
    target_keywords=["AI agents", "multi-agent systems"]
)
```

## 📋 Management & Coordination Agents

### 9. ProjectManager 📅
**Specialty:** Project planning and coordination

**Key Methods:**
- `create_project_plan(project_name, requirements, deadline, team_size)` - Project planning
- `prioritize_tasks(tasks)` - Task prioritization
- `allocate_resources(tasks, team_members)` - Resource allocation
- `track_progress(project_data)` - Progress tracking

**Best For:**
- Sprint planning
- Resource management
- Timeline estimation
- Risk assessment

**Example:**
```python
from agenticraft.agents.specialized import ProjectManager

pm = ProjectManager()
project_plan = await pm.create_project_plan(
    "Mobile App Development",
    requirements=["User authentication", "Dashboard", "Notifications"],
    deadline="2024-06-30",
    team_size=5
)
```

## 🎯 Combining Agents in Workflows

### Example: Complete Software Development Team

```python
from agenticraft.agents.specialized import (
    BusinessAnalyst, ProjectManager, DevOpsEngineer,
    CodeReviewer, QATester, TechnicalWriter
)

# 1. Analyze requirements
ba = BusinessAnalyst()
requirements = await ba.analyze_requirements(project_description)

# 2. Create project plan
pm = ProjectManager()
plan = await pm.create_project_plan(
    project_name="CRM System",
    requirements=requirements["requirements"]["functional"],
    team_size=8
)

# 3. Setup CI/CD
devops = DevOpsEngineer()
pipeline = await devops.generate_ci_cd_pipeline("python", "github")

# 4. Review code quality
reviewer = CodeReviewer()
review = await reviewer.review_code(implementation, "python")

# 5. Test the system
qa = QATester()
test_results = await qa.create_test_plan(
    "CRM System",
    features=["Contact Management", "Sales Pipeline"]
)

# 6. Document everything
writer = TechnicalWriter()
docs = await writer.write_documentation("CRM System", "end-users")
```

### Example: Content Creation Pipeline

```python
from agenticraft.agents.specialized import (
    WebResearcher, DataAnalyst, TechnicalWriter, SEOSpecialist
)

# 1. Research topic
researcher = WebResearcher()
research = await researcher.research("Cloud Computing Trends 2024")

# 2. Analyze data
analyst = DataAnalyst()
insights = await analyst.generate_insights(research["statistics"])

# 3. Write content
writer = TechnicalWriter()
article = await writer.write_article(
    topic="Cloud Computing Trends",
    research=research,
    insights=insights
)

# 4. Optimize for SEO
seo = SEOSpecialist()
optimized = await seo.analyze_content(
    article,
    target_keywords=["cloud computing", "cloud trends", "2024"]
)
```

## 🔧 Agent Customization

All agents can be customized with personality traits:

```python
# Create a more creative technical writer
creative_writer = TechnicalWriter(
    name="Creative Tech Writer",
    personality_traits={
        "analytical": 0.7,
        "creative": 0.9,  # Increased creativity
        "precise": 0.8,
        "empathetic": 0.8,
        "patient": 0.7
    }
)

# Create a more cautious DevOps engineer
careful_devops = DevOpsEngineer(
    name="Careful DevOps",
    personality_traits={
        "systematic": 0.9,
        "reliable": 0.9,
        "efficient": 0.7,
        "cautious": 0.9,  # Increased caution
        "innovative": 0.5
    }
)
```

## 📊 Agent Comparison Matrix

| Agent | Primary Focus | Key Strength | Best Used For |
|-------|--------------|--------------|---------------|
| WebResearcher | Information gathering | Comprehensive research | Market analysis, fact-finding |
| DataAnalyst | Data insights | Statistical analysis | Reports, trends, predictions |
| BusinessAnalyst | Requirements | Process optimization | Planning, gap analysis |
| CodeReviewer | Code quality | Security & best practices | PR reviews, audits |
| DevOpsEngineer | Infrastructure | Automation | Deployments, CI/CD |
| QATester | Quality assurance | Test coverage | Bug prevention, testing |
| TechnicalWriter | Documentation | Clear communication | Docs, tutorials |
| SEOSpecialist | Search optimization | Visibility | Content strategy |
| ProjectManager | Coordination | Resource planning | Team management |

## 🚀 Getting Started

1. **Import the agent you need:**
   ```python
   from agenticraft.agents.specialized import AgentName
   ```

2. **Create an instance:**
   ```python
   agent = AgentName(name="Custom Name")
   ```

3. **Use the agent's methods:**
   ```python
   result = await agent.method_name(parameters)
   ```

4. **Access reasoning transparency:**
   ```python
   reasoning = agent.last_reasoning
   print(reasoning.thoughts)
   ```

## 💡 Best Practices

1. **Choose the right agent** - Each agent is optimized for specific tasks
2. **Combine agents** - Create powerful workflows by combining multiple agents
3. **Customize personalities** - Adjust traits to match your needs
4. **Monitor reasoning** - Use transparency features to understand decisions
5. **Handle errors gracefully** - All agents provide detailed error information

## 🔗 Integration with Hero Workflows

All specialized agents can be integrated into the three hero workflows:

- **Research Team**: Add SEOSpecialist for content optimization
- **Customer Service**: Add BusinessAnalyst for process improvement
- **Code Review**: Add QATester for comprehensive quality checks

See the [Hero Workflows Guide](../heroes/README.md) for integration examples.
