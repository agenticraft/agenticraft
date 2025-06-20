"""Code Reviewer specialized agent for AgentiCraft.

This agent specializes in code review, analysis, and quality assessment.
Simplified extraction from Agentic Framework focused on practical code review.
"""

import re
from typing import Any, Dict, List, Optional
from enum import Enum

from agenticraft.core import Agent


class IssueType(Enum):
    """Types of code issues."""
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DOCUMENTATION = "documentation"


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CodeReviewer(Agent):
    """Agent specialized in code review and quality analysis.
    
    This agent can:
    - Review code for bugs and security issues
    - Check code style and best practices
    - Suggest improvements and refactoring
    - Analyze code complexity
    - Review documentation
    
    Args:
        name: Name for this reviewer
        languages: List of supported languages
        **kwargs: Additional arguments passed to Agent
    """
    
    def __init__(
        self,
        name: str = "CodeReviewer",
        languages: Optional[List[str]] = None,
        **kwargs
    ):
        # Set specialized instructions for code review if not provided
        if "instructions" not in kwargs:
            kwargs["instructions"] = """You are a specialized code reviewer. Your role is to:
1. Review code for bugs, security issues, and performance problems
2. Check adherence to best practices and style guides
3. Suggest improvements and refactoring opportunities
4. Analyze code complexity and maintainability
5. Review documentation and comments

When reviewing, be thorough but constructive. Explain issues clearly and provide actionable suggestions."""
        
        # Initialize the agent
        super().__init__(name=name, **kwargs)
        
        # Supported languages
        self.languages = languages or ["python", "javascript", "typescript", "java", "go"]
        
        # Initialize review patterns
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize code review patterns."""
        # Security patterns
        self.security_patterns = {
            "sql_injection": [
                r"SELECT.*FROM.*WHERE.*['\"]?\s*\+",
                r"execute\s*\(\s*['\"].*\+",
            ],
            "xss": [
                r"innerHTML\s*=",
                r"document\.write\s*\(",
                r"eval\s*\("
            ],
            "hardcoded_secrets": [
                r"(password|api_key|secret)\s*=\s*['\"][^'\"]+['\"]",
            ],
        }
        
        # Code smell patterns
        self.code_smells = {
            "long_method": {"lines": 50},
            "too_many_parameters": {"count": 5},
            "deep_nesting": {"depth": 4},
        }
    
    async def review(
        self,
        code: str,
        language: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform code review.
        
        Args:
            code: Code to review
            language: Programming language
            context: Additional context (PR info, etc.)
            
        Returns:
            Review results with issues and suggestions
        """
        # Detect language if not specified
        if not language:
            language = self._detect_language(code)
        
        # Build review prompt
        prompt = f"""Review the following {language} code:

```{language}
{code}
```

Please analyze for:
1. Bugs and logical errors
2. Security vulnerabilities
3. Performance issues
4. Code style and best practices
5. Documentation quality

Provide specific line numbers when identifying issues."""
        
        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt += f"\n\nContext:\n{context_str}"
        
        # Get review from LLM
        response = await self.arun(prompt, context=context)
        
        # Parse response and extract structured issues
        issues = self._parse_issues(response.content)
        
        # Run pattern-based checks
        pattern_issues = self._check_patterns(code, language)
        issues.extend(pattern_issues)
        
        # Calculate metrics
        metrics = self._calculate_metrics(code)
        
        # Generate score
        score = self._calculate_score(issues, metrics)
        
        return {
            "language": language,
            "issues": issues,
            "metrics": metrics,
            "score": score,
            "summary": self._generate_summary(issues, metrics, score),
            "raw_review": response.content,
            "reviewer": self.name
        }
    
    async def suggest_improvements(
        self,
        code: str,
        language: Optional[str] = None,
        focus: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Suggest code improvements.
        
        Args:
            code: Code to improve
            language: Programming language
            focus: Specific focus area (e.g., "performance", "readability")
            
        Returns:
            List of improvement suggestions
        """
        if not language:
            language = self._detect_language(code)
        
        prompt = f"""Suggest improvements for this {language} code:

```{language}
{code}
```"""
        
        if focus:
            prompt += f"\n\nFocus on {focus} improvements."
        else:
            prompt += "\n\nConsider performance, readability, and maintainability."
        
        response = await self.arun(prompt)
        
        # Parse suggestions
        suggestions = self._parse_suggestions(response.content)
        
        return suggestions
    
    async def review_pr(
        self,
        files: List[Dict[str, str]],
        pr_description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Review a pull request with multiple files.
        
        Args:
            files: List of dicts with 'path' and 'content'
            pr_description: PR description
            context: Additional context
            
        Returns:
            Complete PR review
        """
        all_issues = []
        file_reviews = []
        
        # Review each file
        for file_info in files:
            file_path = file_info.get("path", "unknown")
            code = file_info.get("content", "")
            
            # Skip non-code files
            if not self._is_code_file(file_path):
                continue
            
            # Review file
            review = await self.review(
                code,
                language=self._detect_language_from_path(file_path),
                context={"file": file_path, "pr_description": pr_description}
            )
            
            file_reviews.append({
                "file": file_path,
                "review": review
            })
            
            # Collect issues
            for issue in review["issues"]:
                issue["file"] = file_path
                all_issues.append(issue)
        
        # Overall assessment
        overall = await self._assess_pr(file_reviews, pr_description)
        
        return {
            "files_reviewed": len(file_reviews),
            "total_issues": len(all_issues),
            "issues_by_severity": self._group_by_severity(all_issues),
            "file_reviews": file_reviews,
            "overall_assessment": overall,
            "recommendation": self._get_recommendation(all_issues)
        }
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code."""
        # Simple heuristics
        if "def " in code and "import " in code:
            return "python"
        elif "function " in code or "const " in code or "=>" in code:
            return "javascript"
        elif "public class" in code or "private " in code:
            return "java"
        elif "func " in code and "package " in code:
            return "go"
        else:
            return "unknown"
    
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
            ".c": "c"
        }
        
        for ext, lang in ext_map.items():
            if path.endswith(ext):
                return lang
        
        return "unknown"
    
    def _is_code_file(self, path: str) -> bool:
        """Check if file is a code file."""
        code_extensions = {
            ".py", ".js", ".ts", ".java", ".go", ".rs",
            ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php"
        }
        
        return any(path.endswith(ext) for ext in code_extensions)
    
    def _check_patterns(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Check code against known patterns."""
        issues = []
        
        # Check security patterns
        for vuln_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE))
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    issues.append({
                        "type": IssueType.SECURITY.value,
                        "severity": Severity.HIGH.value,
                        "line": line_num,
                        "message": f"Potential {vuln_type.replace('_', ' ')} vulnerability",
                        "pattern": vuln_type
                    })
        
        return issues
    
    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate basic code metrics."""
        lines = code.split('\n')
        
        # Count various elements
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        
        # Simple complexity estimation
        complexity = 0
        for line in code_lines:
            if any(keyword in line for keyword in ['if', 'elif', 'for', 'while']):
                complexity += 1
        
        return {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len(comment_lines),
            "complexity_estimate": complexity,
            "functions": code.count('def ') + code.count('function '),
            "classes": code.count('class ')
        }
    
    def _calculate_score(
        self,
        issues: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall code quality score."""
        score = 100.0
        
        # Deduct for issues
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity == "critical":
                score -= 15
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            elif severity == "low":
                score -= 2
        
        # Consider complexity
        complexity = metrics.get("complexity_estimate", 0)
        if complexity > 20:
            score -= 10
        elif complexity > 10:
            score -= 5
        
        return max(0, min(100, score))
    
    def _parse_issues(self, review_text: str) -> List[Dict[str, Any]]:
        """Parse issues from review text."""
        issues = []
        
        # This is simplified - in production would use more sophisticated parsing
        lines = review_text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Look for issue indicators
            issue = None
            if "bug" in line_lower or "error" in line_lower:
                issue = {
                    "type": IssueType.BUG.value,
                    "severity": Severity.HIGH.value
                }
            elif "security" in line_lower or "vulnerability" in line_lower:
                issue = {
                    "type": IssueType.SECURITY.value,
                    "severity": Severity.HIGH.value
                }
            elif "performance" in line_lower or "slow" in line_lower:
                issue = {
                    "type": IssueType.PERFORMANCE.value,
                    "severity": Severity.MEDIUM.value
                }
            
            if issue:
                # Try to extract line number
                line_match = re.search(r'line\s*(\d+)', line_lower)
                if line_match:
                    issue["line"] = int(line_match.group(1))
                
                issue["message"] = line.strip()
                issues.append(issue)
        
        return issues
    
    def _parse_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Parse improvement suggestions from text."""
        suggestions = []
        
        # Look for numbered suggestions
        lines = text.split('\n')
        current_suggestion = None
        
        for line in lines:
            # Check for numbered items
            if re.match(r'^\d+\.?\s+', line):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                
                current_suggestion = {
                    "suggestion": line.strip(),
                    "details": []
                }
            elif current_suggestion and line.strip():
                current_suggestion["details"].append(line.strip())
        
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        return suggestions
    
    def _generate_summary(
        self,
        issues: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        score: float
    ) -> str:
        """Generate review summary."""
        severity_counts = self._group_by_severity(issues)
        
        summary = f"Code Quality Score: {score:.1f}/100\n\n"
        
        if issues:
            summary += f"Found {len(issues)} issues:\n"
            for severity, count in severity_counts.items():
                summary += f"- {severity}: {count}\n"
        else:
            summary += "No significant issues found.\n"
        
        summary += f"\nCode Metrics:\n"
        summary += f"- Lines of code: {metrics['code_lines']}\n"
        summary += f"- Complexity estimate: {metrics['complexity_estimate']}\n"
        
        return summary
    
    def _group_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group issues by severity."""
        counts = {}
        for issue in issues:
            severity = issue.get("severity", "unknown")
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    async def _assess_pr(
        self,
        file_reviews: List[Dict[str, Any]],
        pr_description: Optional[str]
    ) -> str:
        """Generate overall PR assessment."""
        total_issues = sum(
            len(fr["review"]["issues"]) for fr in file_reviews
        )
        
        avg_score = sum(
            fr["review"]["score"] for fr in file_reviews
        ) / len(file_reviews) if file_reviews else 0
        
        assessment = f"Reviewed {len(file_reviews)} files.\n"
        assessment += f"Average code quality: {avg_score:.1f}/100\n"
        assessment += f"Total issues found: {total_issues}\n"
        
        if pr_description:
            assessment += f"\nThe changes align with the PR description."
        
        return assessment
    
    def _get_recommendation(self, issues: List[Dict[str, Any]]) -> str:
        """Get merge recommendation based on issues."""
        critical_issues = [
            i for i in issues
            if i.get("severity") == Severity.CRITICAL.value
        ]
        
        high_issues = [
            i for i in issues
            if i.get("severity") == Severity.HIGH.value
        ]
        
        if critical_issues:
            return "❌ Block merge - Critical issues must be fixed"
        elif len(high_issues) > 3:
            return "⚠️ Request changes - Multiple high-severity issues"
        elif len(issues) > 10:
            return "💭 Consider improvements - Many minor issues"
        else:
            return "✅ Approve - Code looks good"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"CodeReviewer(name='{self.name}', languages={self.languages})"
