# Code Review Pipeline - Hero Workflow

The CodeReviewPipeline is AgentiCraft's third hero workflow, providing automated code review with specialized agents, GitHub integration, and deployment capabilities.

## 🎯 The Hook

**"Automated code review with specialized agents and deployment"**

```python
from agenticraft.workflows import CodeReviewPipeline

pipeline = CodeReviewPipeline()
review = await pipeline.review(github_pr)
```

## Overview

The CodeReviewPipeline coordinates multiple specialized agents to provide comprehensive code review:

- **Security Reviewer**: Finds vulnerabilities and security issues
- **Performance Reviewer**: Identifies bottlenecks and optimization opportunities  
- **Best Practices Reviewer**: Checks style, patterns, and maintainability
- **Documentation Reviewer**: Ensures proper documentation (thorough mode)
- **Test Reviewer**: Validates test coverage (thorough mode)

## Quick Start

### Basic Code Review

```python
from agenticraft.workflows import CodeReviewPipeline

# Create pipeline
pipeline = CodeReviewPipeline()

# Review code
code = '''
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
'''

review = await pipeline.review(code, language="python")

print(f"Score: {review['aggregated']['average_score']}/100")
print(f"Issues: {len(review['aggregated']['all_issues'])}")
print(f"Deployment: {review['deployment']['status']}")
```

### GitHub PR Review

```python
# Review a GitHub PR
pipeline = CodeReviewPipeline(
    mode="thorough",
    github_app_id="your-app-id",
    github_private_key="your-private-key"
)

review = await pipeline.review_pr(
    pr_url="https://github.com/org/repo/pull/123",
    github_token="your-token"
)

print(review['summary'])  # Formatted PR review summary
print(review['recommendation'])  # Merge recommendation
```

### Generate Deployment

```python
# After successful review, generate K8s deployment
if review['deployment']['status'] == "approved":
    deployment = await pipeline.generate_deployment(
        review,
        deployment_config={
            "app_name": "my-service",
            "image": "myregistry/my-service:v1.0.0",
            "replicas": 3
        }
    )
    
    # Get manifests
    print(deployment['manifests']['deployment'])
    print(deployment['kubectl_commands'])
```

## Review Modes

### Quick Mode (Default)
- 2 agents per file
- Fast feedback for development
- Basic security and style checks

### Standard Mode
- 3 agents per file  
- Balanced depth and speed
- Comprehensive issue detection

### Thorough Mode
- 5 agents per file
- Deep analysis including docs and tests
- Best for critical code and releases

```python
# Configure mode
pipeline = CodeReviewPipeline(mode="thorough")
```

## Features

### Multi-Agent Coordination

The pipeline coordinates specialized reviewers in parallel:

```python
# Each agent focuses on their specialty
SecurityReviewer     → Vulnerabilities, auth issues
PerformanceReviewer  → Bottlenecks, efficiency  
BestPracticesReviewer → Style, patterns, maintainability
DocumentationReviewer → Comments, API docs (thorough mode)
TestReviewer         → Coverage, test quality (thorough mode)
```

### Issue Aggregation

Issues from all reviewers are:
- Deduplicated automatically
- Grouped by severity (critical/high/medium/low/info)
- Scored for overall quality (0-100)

### Consensus Calculation

The pipeline calculates reviewer agreement:
- **High consensus**: Low variance in scores
- **Medium consensus**: Moderate variance
- **Low consensus**: High variance (may need human review)

### Deployment Readiness

Automatic assessment based on:
- **Approved**: Score > 60, no blocking issues
- **Manual Review**: Score < 60
- **Blocked**: Critical or high-severity issues

## Configuration

### Basic Configuration

```python
pipeline = CodeReviewPipeline(
    name="MyReviewPipeline",
    mode="standard",
    agents_per_file=3,
    model="gpt-4",
    provider="openai"
)
```

### GitHub Integration

```python
# Using GitHub App authentication
pipeline = CodeReviewPipeline(
    github_app_id="123456",
    github_private_key="""-----BEGIN RSA PRIVATE KEY-----
    ...your key...
    -----END RSA PRIVATE KEY-----"""
)

# Review PR with auto-comment
review = await pipeline.review_pr(
    pr_url="https://github.com/org/repo/pull/123",
    github_token="ghp_..."  # For posting comments
)
```

### Custom Review Focus

```python
# Focus on specific aspects
suggestions = await pipeline.reviewers[0].suggest_improvements(
    code=code,
    language="python", 
    focus="performance"  # or "readability", "security"
)
```

## Integration Examples

### FastAPI Webhook Receiver

```python
from fastapi import FastAPI, HTTPException
from agenticraft.workflows import CodeReviewPipeline

app = FastAPI()
pipeline = CodeReviewPipeline(mode="standard")

@app.post("/webhook/github")
async def github_webhook(payload: dict):
    """Receive GitHub PR webhook."""
    if payload.get("action") == "opened":
        pr_number = payload["pull_request"]["number"]
        repo = payload["repository"]["full_name"]
        
        review = await pipeline.review_pr(
            pr_number=pr_number,
            repo=repo,
            github_token=os.getenv("GITHUB_TOKEN")
        )
        
        return {"status": "reviewed", "recommendation": review["recommendation"]}
```

### CI/CD Integration

```python
# In your CI pipeline (e.g., GitHub Actions)
import sys

async def ci_review():
    pipeline = CodeReviewPipeline(mode="thorough")
    
    # Get changed files from CI environment
    changed_files = get_changed_files()  # Your CI logic
    
    # Review files
    review = await pipeline.review_pr(files=changed_files)
    
    # Exit with appropriate code
    if review["recommendation"].startswith("❌"):
        print("Code review failed - blocking merge")
        sys.exit(1)
    else:
        print("Code review passed")
        sys.exit(0)
```

### Kubernetes Deployment

```python
# After successful review
async def deploy_if_approved(review_results):
    if review_results["deployment"]["status"] != "approved":
        print("Deployment blocked due to code quality issues")
        return
    
    deployment = await pipeline.generate_deployment(
        review_results,
        deployment_config={
            "app_name": "my-app",
            "image": f"myregistry/my-app:{git_sha}",
            "replicas": 3,
            "expose_externally": True,
            "domain": "api.example.com"
        }
    )
    
    # Apply manifests
    for manifest_type, content in deployment["manifests"].items():
        with open(f"{manifest_type}.yaml", "w") as f:
            f.write(content)
    
    # Show kubectl commands
    print("\nRun these commands to deploy:")
    for cmd in deployment["kubectl_commands"]:
        print(f"  {cmd}")
```

## Best Practices

### 1. Choose the Right Mode

- **Development**: Use `quick` mode for rapid iteration
- **Pull Requests**: Use `standard` mode for regular PRs
- **Releases**: Use `thorough` mode for production releases

### 2. Handle Large PRs

```python
# For large PRs, review in batches
async def review_large_pr(files):
    batch_size = 10
    all_reviews = []
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        review = await pipeline.review_pr(files=batch)
        all_reviews.append(review)
    
    # Aggregate results
    return aggregate_reviews(all_reviews)
```

### 3. Custom Security Policies

```python
# Add custom security patterns
reviewer = pipeline.reviewers[0]  # SecurityReviewer
reviewer.security_patterns["custom_vuln"] = [
    r"exec\s*\(",  # Dangerous exec usage
    r"pickle\.loads",  # Unsafe deserialization
]
```

### 4. Integrate with Existing Tools

```python
# Export results for other tools
def export_sarif(review_results):
    """Export to SARIF format for GitHub Security tab."""
    sarif = {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "AgentiCraft"}},
            "results": [
                {
                    "ruleId": issue["type"],
                    "level": issue["severity"],
                    "message": {"text": issue["message"]},
                    "locations": [...]
                }
                for issue in review_results["aggregated"]["all_issues"]
            ]
        }]
    }
    return sarif
```

## Architecture

### Pipeline Flow

```
1. Code Input → Parse & Detect Language
2. Distribute to Specialized Reviewers (Parallel)
3. Each Reviewer Analyzes Code
4. Aggregate Results & Deduplicate
5. Calculate Consensus & Score
6. Assess Deployment Readiness
7. Generate Recommendations
```

### Review Process

```python
# Internal review process
async def review_file(file_content, language):
    # 1. Create review tasks for each agent
    tasks = [
        agent.review(file_content, language)
        for agent in selected_agents
    ]
    
    # 2. Run reviews in parallel
    reviews = await asyncio.gather(*tasks)
    
    # 3. Aggregate results
    aggregated = aggregate_reviews(reviews)
    
    # 4. Calculate consensus
    consensus = calculate_consensus(reviews)
    
    # 5. Determine deployment status
    deployment = assess_deployment(aggregated)
    
    return {
        "reviews": reviews,
        "aggregated": aggregated,
        "consensus": consensus,
        "deployment": deployment
    }
```

## Customization

### Add Custom Reviewers

```python
from agenticraft.agents.specialized import CodeReviewer

class ComplianceReviewer(CodeReviewer):
    """Check regulatory compliance."""
    
    def __init__(self, regulations=None, **kwargs):
        super().__init__(
            name="ComplianceReviewer",
            instructions="Check code for regulatory compliance...",
            **kwargs
        )
        self.regulations = regulations or ["GDPR", "HIPAA"]

# Add to pipeline
pipeline.reviewers.append(ComplianceReviewer())
```

### Custom Scoring

```python
# Override scoring logic
def custom_score(issues, metrics):
    score = 100
    
    # Custom weights
    weights = {
        "critical": 20,
        "high": 10,
        "medium": 3,
        "low": 1
    }
    
    for issue in issues:
        severity = issue.get("severity", "low")
        score -= weights.get(severity, 1)
    
    # Bonus for good documentation
    if metrics["comment_lines"] / metrics["total_lines"] > 0.2:
        score += 5
    
    return max(0, min(100, score))

pipeline._calculate_score = custom_score
```

## Monitoring

The pipeline includes built-in telemetry:

```python
# Metrics tracked
- review_duration: Time to complete review
- issues_found: Number of issues detected
- consensus_variance: Agreement between reviewers
- deployment_decisions: Approved/blocked/manual

# Traces include
- Individual reviewer performance
- Aggregation time
- GitHub API calls
```

## Troubleshooting

### Slow Reviews

```python
# Use quick mode for faster feedback
pipeline = CodeReviewPipeline(mode="quick")

# Or reduce agents per file
pipeline = CodeReviewPipeline(agents_per_file=1)
```

### Inconsistent Results

```python
# Check consensus level
if review["consensus"]["level"] == "low":
    # High variance - consider human review
    print("Reviewers disagree significantly")
    print(review["consensus"]["reviewer_scores"])
```

### GitHub Integration Issues

```python
# Verify GitHub authentication
try:
    review = await pipeline.review_pr(...)
except Exception as e:
    print(f"GitHub error: {e}")
    # Check app permissions, token validity
```

## Summary

The CodeReviewPipeline provides:

- ✅ **Multi-agent code review** with specialized focus areas
- ✅ **GitHub integration** for automated PR reviews
- ✅ **Deployment readiness** assessment
- ✅ **Kubernetes manifest** generation
- ✅ **Flexible modes** for different use cases
- ✅ **Production-ready** with auth and monitoring

Perfect for teams wanting to automate code quality checks while maintaining high standards for security, performance, and best practices.
