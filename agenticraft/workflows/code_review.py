"""Code Review Pipeline Hero Workflow for AgentiCraft.

This workflow provides automated code review with specialized agents,
GitHub integration, and deployment capabilities.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime

from agenticraft.core import Workflow
from agenticraft.agents.specialized.code_reviewer import CodeReviewer
from agenticraft.agents.patterns.coordinator import SimpleCoordinator
# from agenticraft.providers import get_provider  # TODO: Implement provider factory
# from agenticraft.telemetry import create_span, set_span_attributes, record_latency, record_error  # TODO: Implement telemetry
from agenticraft.core.auth import JWTAuth, APIKeyAuth

# Temporary telemetry stubs
class DummySpan:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

def create_span(name: str):
    return DummySpan()

def set_span_attributes(attrs: dict):
    pass

def record_latency(service: str, latency: float):
    pass

def record_error(service: str, error: Exception):
    pass


class ReviewMode(Enum):
    """Code review modes."""
    QUICK = "quick"      # Fast review for small changes
    STANDARD = "standard"  # Normal review depth
    THOROUGH = "thorough"  # Deep analysis for critical code


class DeploymentStatus(Enum):
    """Deployment status after review."""
    APPROVED = "approved"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"


class CodeReviewPipeline(Workflow):
    """Automated code review pipeline with multi-agent coordination.
    
    This hero workflow provides:
    - Multi-agent code review with different specializations
    - GitHub integration for PR reviews
    - Security and performance analysis
    - Deployment readiness assessment
    - Kubernetes deployment generation
    
    Example:
        ```python
        from agenticraft.workflows import CodeReviewPipeline
        
        # Quick setup
        pipeline = CodeReviewPipeline()
        
        # Review a PR
        review = await pipeline.review_pr(
            pr_url="https://github.com/org/repo/pull/123",
            github_token="your-token"
        )
        
        # Review code directly
        review = await pipeline.review(
            code="def hello(): print('world')",
            language="python"
        )
        ```
    
    Args:
        name: Pipeline name
        mode: Review mode - accepts ReviewMode enum or string ('quick'/'standard'/'thorough')
        agents_per_file: Number of agents to review each file
        model: LLM model to use
        provider: LLM provider
        github_app_id: GitHub App ID for authentication
        github_private_key: GitHub App private key
        **kwargs: Additional workflow arguments
    """
    
    def __init__(
        self,
        name: str = "CodeReviewPipeline",
        mode: ReviewMode = ReviewMode.STANDARD,
        agents_per_file: int = 2,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        github_app_id: Optional[str] = None,
        github_private_key: Optional[str] = None,
        **kwargs
    ):
        # Extract workflow-specific kwargs
        workflow_kwargs = {}
        if 'description' in kwargs:
            workflow_kwargs['description'] = kwargs.pop('description')
        
        # Initialize workflow with only supported args
        super().__init__(name=name, **workflow_kwargs)
        
        # Store any remaining kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Handle mode as either enum or string
        if isinstance(mode, str):
            self.mode = ReviewMode(mode)
        else:
            self.mode = mode
        self.agents_per_file = agents_per_file
        self.model = model
        self.provider_name = provider
        
        # GitHub configuration
        self.github_app_id = github_app_id
        self.github_private_key = github_private_key
        
        # Initialize components
        self._setup_agents()
        self._setup_auth()
        
        # Telemetry service name
        self.service_name = "code_review_pipeline"
    
    def _setup_agents(self):
        """Set up the review team."""
        # Get provider (TODO: implement provider factory)
        provider = None  # get_provider(self.provider_name) if self.provider_name else None
        
        # Use default model from settings if not specified
        from agenticraft.core.config import settings
        model = self.model or settings.default_model
        
        # Create specialized reviewers
        self.reviewers = []
        
        # Security-focused reviewer
        self.reviewers.append(
            CodeReviewer(
                name="SecurityReviewer",
                model=model,
                provider=provider,
                instructions="""You are a security-focused code reviewer. 
                Prioritize finding security vulnerabilities, authentication issues,
                data exposure risks, and injection attacks."""
            )
        )
        
        # Performance-focused reviewer
        self.reviewers.append(
            CodeReviewer(
                name="PerformanceReviewer",
                model=model,
                provider=provider,
                instructions="""You are a performance-focused code reviewer.
                Look for performance bottlenecks, inefficient algorithms,
                memory leaks, and optimization opportunities."""
            )
        )
        
        # Best practices reviewer
        self.reviewers.append(
            CodeReviewer(
                name="BestPracticesReviewer",
                model=model,
                provider=provider,
                instructions="""You are a best practices code reviewer.
                Check for code style, design patterns, maintainability,
                and adherence to language-specific conventions."""
            )
        )
        
        # Add more reviewers based on mode
        if self.mode == ReviewMode.THOROUGH:
            # Documentation reviewer
            self.reviewers.append(
                CodeReviewer(
                    name="DocumentationReviewer",
                    model=model,
                    provider=provider,
                    instructions="""You are a documentation-focused reviewer.
                    Check for missing documentation, unclear comments,
                    and API documentation completeness."""
                )
            )
            
            # Test coverage reviewer
            self.reviewers.append(
                CodeReviewer(
                    name="TestReviewer",
                    model=model,
                    provider=provider,
                    instructions="""You are a testing-focused reviewer.
                    Look for missing tests, test coverage gaps,
                    and test quality issues."""
                )
            )
        
        # Set up coordinator
        self.coordinator = SimpleCoordinator(
            agents=self.reviewers[:self.agents_per_file],
            name=f"{self.name}_Coordinator"
        )
    
    def _setup_auth(self):
        """Set up authentication handlers."""
        # API key auth for webhook validation
        self.api_auth = APIKeyAuth()
        
        # JWT auth for GitHub App
        if self.github_app_id and self.github_private_key:
            self.jwt_auth = JWTAuth(
                app_id=self.github_app_id,
                private_key=self.github_private_key
            )
    
    async def review(
        self,
        code: str,
        language: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Review code with the pipeline.
        
        Args:
            code: Code to review
            language: Programming language
            context: Additional context
            
        Returns:
            Comprehensive review results
        """
        with create_span(f"{self.service_name}.code_review") as span:
            set_span_attributes({
                "language": language or "unknown",
                "mode": self.mode.value,
                "code_lines": len(code.split('\n'))
            })
            
            # Track start time
            start_time = datetime.now()
            
            # Coordinate reviews
            review_tasks = []
            for reviewer in self.reviewers[:self.agents_per_file]:
                task = reviewer.review(code, language, context)
                review_tasks.append(task)
            
            # Run reviews in parallel
            reviews = await asyncio.gather(*review_tasks)
            
            # Aggregate results
            aggregated = self._aggregate_reviews(reviews)
            
            # Calculate consensus
            consensus = self._calculate_consensus(reviews)
            
            # Generate deployment recommendation
            deployment = self._assess_deployment_readiness(aggregated)
            
            # Track metrics
            duration = (datetime.now() - start_time).total_seconds()
            record_latency(self.service_name, duration * 1000)  # Convert to ms
            set_span_attributes({
                "review_duration": duration,
                "issues_found": len(aggregated["all_issues"])
            })
            
            return {
                "individual_reviews": reviews,
                "aggregated": aggregated,
                "consensus": consensus,
                "deployment": deployment,
                "duration": duration,
                "mode": self.mode.value,
                "pipeline_reasoning": self._get_reasoning()
            }
    
    async def review_pr(
        self,
        pr_url: Optional[str] = None,
        pr_number: Optional[int] = None,
        repo: Optional[str] = None,
        github_token: Optional[str] = None,
        files: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Review a GitHub pull request.
        
        Args:
            pr_url: Full PR URL
            pr_number: PR number (if repo provided)
            repo: Repository in format "owner/repo"
            github_token: GitHub access token
            files: Optional list of files (if not fetching from GitHub)
            
        Returns:
            Complete PR review
        """
        with create_span(f"{self.service_name}.pr_review") as span:
            # Parse PR info
            if pr_url:
                pr_info = self._parse_pr_url(pr_url)
                repo = pr_info["repo"]
                pr_number = pr_info["number"]
            
            set_span_attributes({
                "repo": repo,
                "pr_number": pr_number
            })
            
            # Fetch PR data if not provided
            if not files and github_token:
                files = await self._fetch_pr_files(
                    repo, pr_number, github_token
                )
            
            if not files:
                return {
                    "error": "No files to review",
                    "repo": repo,
                    "pr_number": pr_number
                }
            
            # Review each file
            file_reviews = []
            all_issues = []
            
            for file_info in files:
                if not self._should_review_file(file_info["path"]):
                    continue
                
                # Review file
                review = await self.review(
                    code=file_info["content"],
                    language=self._detect_language_from_path(file_info["path"]),
                    context={
                        "file": file_info["path"],
                        "pr": pr_number,
                        "repo": repo
                    }
                )
                
                file_reviews.append({
                    "file": file_info["path"],
                    "review": review
                })
                
                # Collect issues
                all_issues.extend(review["aggregated"]["all_issues"])
            
            # Generate PR summary
            pr_summary = self._generate_pr_summary(file_reviews, all_issues)
            
            # Create GitHub comment if token provided
            comment = None
            if github_token:
                comment = await self._post_github_comment(
                    repo, pr_number, pr_summary, github_token
                )
            
            return {
                "repo": repo,
                "pr_number": pr_number,
                "files_reviewed": len(file_reviews),
                "total_issues": len(all_issues),
                "file_reviews": file_reviews,
                "summary": pr_summary,
                "github_comment": comment,
                "recommendation": self._get_pr_recommendation(all_issues)
            }
    
    async def generate_deployment(
        self,
        review_results: Dict[str, Any],
        deployment_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Kubernetes deployment based on review.
        
        Args:
            review_results: Results from review or review_pr
            deployment_config: Optional deployment configuration
            
        Returns:
            Deployment manifests and configuration
        """
        # Check if deployment is approved
        deployment_status = review_results.get("deployment", {}).get("status")
        
        if deployment_status == DeploymentStatus.BLOCKED.value:
            return {
                "status": "blocked",
                "reason": "Code review found blocking issues",
                "issues": review_results.get("aggregated", {}).get("blocking_issues", [])
            }
        
        # Generate deployment manifests
        config = deployment_config or {}
        
        manifests = {
            "deployment": self._generate_deployment_manifest(config),
            "service": self._generate_service_manifest(config),
            "configmap": self._generate_configmap_manifest(config),
        }
        
        # Add ingress if specified
        if config.get("expose_externally"):
            manifests["ingress"] = self._generate_ingress_manifest(config)
        
        return {
            "status": "ready",
            "manifests": manifests,
            "deployment_notes": self._generate_deployment_notes(review_results),
            "kubectl_commands": self._generate_kubectl_commands(manifests)
        }
    
    def _aggregate_reviews(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple reviews into a unified result."""
        all_issues = []
        all_suggestions = []
        scores = []
        
        for review in reviews:
            all_issues.extend(review.get("issues", []))
            all_suggestions.extend(review.get("suggestions", []))
            scores.append(review.get("score", 0))
        
        # Deduplicate issues
        unique_issues = self._deduplicate_issues(all_issues)
        
        # Calculate aggregate score
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Group by severity
        severity_groups = {}
        for issue in unique_issues:
            severity = issue.get("severity", "unknown")
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(issue)
        
        return {
            "all_issues": unique_issues,
            "suggestions": all_suggestions,
            "average_score": avg_score,
            "severity_breakdown": severity_groups,
            "blocking_issues": severity_groups.get("critical", []) + severity_groups.get("high", [])
        }
    
    def _calculate_consensus(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consensus among reviewers."""
        scores = [r.get("score", 0) for r in reviews]
        
        # Calculate variance
        avg_score = sum(scores) / len(scores) if scores else 0
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 0
        
        # High consensus if low variance
        consensus_level = "high" if variance < 100 else "medium" if variance < 400 else "low"
        
        return {
            "level": consensus_level,
            "average_score": avg_score,
            "score_variance": variance,
            "reviewer_scores": {
                reviews[i].get("reviewer", f"Reviewer{i+1}"): scores[i]
                for i in range(len(reviews))
            }
        }
    
    def _assess_deployment_readiness(
        self,
        aggregated: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess if code is ready for deployment."""
        blocking_issues = aggregated.get("blocking_issues", [])
        avg_score = aggregated.get("average_score", 0)
        
        if blocking_issues:
            status = DeploymentStatus.BLOCKED
            reason = f"Found {len(blocking_issues)} blocking issues"
        elif avg_score < 60:
            status = DeploymentStatus.MANUAL_REVIEW
            reason = f"Low quality score: {avg_score:.1f}"
        else:
            status = DeploymentStatus.APPROVED
            reason = "Code meets quality standards"
        
        return {
            "status": status.value,
            "reason": reason,
            "score": avg_score,
            "blocking_issues": len(blocking_issues)
        }
    
    def _deduplicate_issues(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate issues."""
        seen = set()
        unique = []
        
        for issue in issues:
            # Create a key from issue properties
            key = (
                issue.get("type"),
                issue.get("line"),
                issue.get("message", "")[:50]  # First 50 chars
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(issue)
        
        return unique
    
    def _parse_pr_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub PR URL."""
        # Example: https://github.com/owner/repo/pull/123
        parts = url.strip("/").split("/")
        
        if len(parts) >= 7 and parts[5] == "pull":
            return {
                "owner": parts[3],
                "repo": f"{parts[3]}/{parts[4]}",
                "number": int(parts[6])
            }
        
        raise ValueError(f"Invalid PR URL: {url}")
    
    def _should_review_file(self, path: str) -> bool:
        """Check if file should be reviewed."""
        # Skip non-code files
        skip_extensions = {
            ".md", ".txt", ".json", ".yaml", ".yml",
            ".lock", ".png", ".jpg", ".gif", ".svg"
        }
        
        return not any(path.endswith(ext) for ext in skip_extensions)
    
    def _detect_language_from_path(self, path: str) -> str:
        """Detect language from file path."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php"
        }
        
        for ext, lang in ext_map.items():
            if path.endswith(ext):
                return lang
        
        return "unknown"
    
    async def _fetch_pr_files(
        self,
        repo: str,
        pr_number: int,
        token: str
    ) -> List[Dict[str, str]]:
        """Fetch PR files from GitHub."""
        # This would use GitHub API
        # Simplified for example
        return []
    
    def _generate_pr_summary(
        self,
        file_reviews: List[Dict[str, Any]],
        all_issues: List[Dict[str, Any]]
    ) -> str:
        """Generate PR review summary."""
        total_files = len(file_reviews)
        
        # Count by severity
        severity_counts = {}
        for issue in all_issues:
            severity = issue.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Build summary
        summary = f"## 🔍 Code Review Summary\n\n"
        summary += f"Reviewed **{total_files}** files using {self.mode.value} mode.\n\n"
        
        if all_issues:
            summary += f"### 📊 Issues Found: {len(all_issues)}\n\n"
            for severity, count in sorted(severity_counts.items()):
                emoji = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "💡",
                    "low": "💭",
                    "info": "ℹ️"
                }.get(severity, "•")
                summary += f"- {emoji} **{severity.title()}**: {count}\n"
        else:
            summary += "### ✅ No issues found!\n"
        
        # Add recommendation
        recommendation = self._get_pr_recommendation(all_issues)
        summary += f"\n### 🎯 Recommendation\n\n{recommendation}\n"
        
        return summary
    
    def _get_pr_recommendation(
        self,
        issues: List[Dict[str, Any]]
    ) -> str:
        """Get PR merge recommendation."""
        critical = sum(1 for i in issues if i.get("severity") == "critical")
        high = sum(1 for i in issues if i.get("severity") == "high")
        
        if critical > 0:
            return "❌ **Block merge** - Critical issues must be resolved"
        elif high > 3:
            return "🔄 **Request changes** - Multiple high-severity issues need attention"
        elif high > 0:
            return "⚠️ **Review suggested** - Some high-severity issues to consider"
        elif len(issues) > 10:
            return "💭 **Consider improvements** - Many minor issues that could be addressed"
        else:
            return "✅ **Approve** - Code meets quality standards"
    
    async def _post_github_comment(
        self,
        repo: str,
        pr_number: int,
        comment: str,
        token: str
    ) -> Dict[str, Any]:
        """Post comment to GitHub PR."""
        # This would use GitHub API
        # Simplified for example
        return {"posted": True, "comment_id": "mock"}
    
    def _generate_deployment_manifest(
        self,
        config: Dict[str, Any]
    ) -> str:
        """Generate Kubernetes deployment manifest."""
        app_name = config.get("app_name", "app")
        image = config.get("image", f"{app_name}:latest")
        replicas = config.get("replicas", 2)
        
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {image}
        ports:
        - containerPort: 8080
"""
    
    def _generate_service_manifest(
        self,
        config: Dict[str, Any]
    ) -> str:
        """Generate Kubernetes service manifest."""
        app_name = config.get("app_name", "app")
        
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service
spec:
  selector:
    app: {app_name}
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
"""
    
    def _generate_configmap_manifest(
        self,
        config: Dict[str, Any]
    ) -> str:
        """Generate Kubernetes configmap manifest."""
        app_name = config.get("app_name", "app")
        
        return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
data:
  environment: "production"
"""
    
    def _generate_ingress_manifest(
        self,
        config: Dict[str, Any]
    ) -> str:
        """Generate Kubernetes ingress manifest."""
        app_name = config.get("app_name", "app")
        domain = config.get("domain", f"{app_name}.example.com")
        
        return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}-ingress
spec:
  rules:
  - host: {domain}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {app_name}-service
            port:
              number: 80
"""
    
    def _generate_deployment_notes(
        self,
        review_results: Dict[str, Any]
    ) -> str:
        """Generate deployment notes based on review."""
        score = review_results.get("aggregated", {}).get("average_score", 0)
        
        notes = f"Deployment generated after code review (score: {score:.1f}/100)\n"
        notes += "Please review the manifests before applying.\n"
        
        if score < 80:
            notes += "\n⚠️ Warning: Code quality score is below 80. Consider addressing issues before deployment."
        
        return notes
    
    def _generate_kubectl_commands(
        self,
        manifests: Dict[str, str]
    ) -> List[str]:
        """Generate kubectl commands for deployment."""
        commands = [
            "# Apply all manifests:",
            "kubectl apply -f deployment.yaml",
            "kubectl apply -f service.yaml",
            "kubectl apply -f configmap.yaml"
        ]
        
        if "ingress" in manifests:
            commands.append("kubectl apply -f ingress.yaml")
        
        commands.extend([
            "",
            "# Check deployment status:",
            "kubectl rollout status deployment/app",
            "kubectl get pods -l app=app"
        ])
        
        return commands
    
    def _get_reasoning(self) -> Dict[str, Any]:
        """Get pipeline reasoning and decision process."""
        return {
            "mode": self.mode.value,
            "agents_used": [r.name for r in self.reviewers[:self.agents_per_file]],
            "coordination_strategy": "parallel review with aggregation",
            "consensus_method": "variance-based agreement",
            "deployment_criteria": {
                "blocked": "critical or high severity issues",
                "manual_review": "score below 60",
                "approved": "score above 60 with no blocking issues"
            }
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CodeReviewPipeline(mode={self.mode.value}, "
            f"agents={self.agents_per_file})"
        )
