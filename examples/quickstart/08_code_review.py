"""Example: Code Review Pipeline - The Third Hero Workflow.

This example demonstrates the CodeReviewPipeline, a multi-agent workflow
that provides automated code review with GitHub integration and deployment capabilities.

Key features:
- Multi-agent code review with different specializations
- Security and performance analysis
- GitHub PR integration
- Deployment manifest generation
"""

import asyncio
import os
from agenticraft.workflows import CodeReviewPipeline
from agenticraft.workflows.code_review import ReviewMode


async def basic_code_review():
    """Basic code review example."""
    print("\n" + "="*50)
    print("Basic Code Review Example")
    print("="*50 + "\n")
    
    # Create pipeline with default mode
    pipeline = CodeReviewPipeline()  # Uses default ReviewMode.STANDARD
    
    # Sample Python code to review
    code = '''
def calculate_factorial(n):
    """Calculate factorial of a number."""
    if n < 0:
        return None
    result = 1
    for i in range(1, n + 1):
        result = result * i
    return result

def process_user_input(user_input):
    """Process user input - potential security issue."""
    # Direct execution of user input - security vulnerability!
    eval(user_input)
    
def inefficient_search(items, target):
    """Inefficient O(n²) search implementation."""
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == target and i == j:
                return i
    return -1
'''
    
    # Run review
    print("🔍 Reviewing code...")
    review = await pipeline.review(code, language="python")
    
    # Display results
    print(f"\n📊 Review Summary:")
    print(f"- Mode: {review['mode']}")
    print(f"- Duration: {review['duration']:.2f} seconds")
    print(f"- Average Score: {review['aggregated']['average_score']:.1f}/100")
    print(f"- Total Issues: {len(review['aggregated']['all_issues'])}")
    
    # Show issues by severity
    print("\n🚨 Issues by Severity:")
    for severity, issues in review['aggregated']['severity_breakdown'].items():
        print(f"- {severity}: {len(issues)}")
    
    # Show consensus
    print(f"\n🤝 Reviewer Consensus: {review['consensus']['level']}")
    
    # Show deployment readiness
    deployment = review['deployment']
    print(f"\n🚀 Deployment Status: {deployment['status']}")
    print(f"   Reason: {deployment['reason']}")


async def github_pr_review():
    """GitHub PR review example."""
    print("\n" + "="*50)
    print("GitHub PR Review Example")
    print("="*50 + "\n")
    
    # Create pipeline with GitHub integration
    pipeline = CodeReviewPipeline(
        mode=ReviewMode.THOROUGH,  # Use thorough mode for PRs
        agents_per_file=3  # More agents for important PRs
    )
    
    # Mock PR files (in real scenario, these would be fetched from GitHub)
    pr_files = [
        {
            "path": "src/auth.py",
            "content": '''
import hashlib

def hash_password(password):
    """Hash password using MD5 - weak algorithm!"""
    return hashlib.md5(password.encode()).hexdigest()

def check_auth(username, password):
    """Check authentication."""
    # Hardcoded credentials - security issue!
    if username == "admin" and password == "admin123":
        return True
    return False
'''
        },
        {
            "path": "src/api.py",
            "content": '''
from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute_command():
    """Execute system command - injection vulnerability!"""
    cmd = request.json.get('command')
    # Direct command execution - dangerous!
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return {'output': result.stdout.decode()}
'''
        }
    ]
    
    # Review PR
    print("🔍 Reviewing Pull Request...")
    pr_review = await pipeline.review_pr(
        pr_number=123,
        repo="example/repo",
        files=pr_files
    )
    
    # Display results
    print(f"\n📊 PR Review Summary:")
    print(f"- Files Reviewed: {pr_review['files_reviewed']}")
    print(f"- Total Issues: {pr_review['total_issues']}")
    print(f"- Recommendation: {pr_review['recommendation']}")
    
    # Show file-specific issues
    print("\n📁 Issues by File:")
    for file_review in pr_review['file_reviews']:
        file_name = file_review['file']
        issues = file_review['review']['aggregated']['all_issues']
        print(f"\n{file_name}: {len(issues)} issues")
        for issue in issues[:2]:  # Show first 2 issues
            print(f"  - {issue.get('severity', 'unknown')}: {issue.get('message', 'No message')}")


async def deployment_generation():
    """Deployment generation example."""
    print("\n" + "="*50)
    print("Deployment Generation Example")
    print("="*50 + "\n")
    
    # Create pipeline
    pipeline = CodeReviewPipeline(mode=ReviewMode.QUICK)
    
    # Review some good code
    good_code = '''
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID with proper error handling."""
        try:
            user = self.db.query(f"SELECT * FROM users WHERE id = ?", [user_id])
            return user
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    def create_user(self, username: str, email: str) -> bool:
        """Create new user with validation."""
        if not self._validate_email(email):
            logger.warning(f"Invalid email: {email}")
            return False
            
        try:
            self.db.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                [username, email]
            )
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def _validate_email(self, email: str) -> bool:
        """Basic email validation."""
        return "@" in email and "." in email
'''
    
    # Review the code
    print("🔍 Reviewing code for deployment...")
    review = await pipeline.review(good_code, language="python")
    
    print(f"✅ Code Score: {review['aggregated']['average_score']:.1f}/100")
    print(f"🚀 Deployment Status: {review['deployment']['status']}")
    
    # Generate deployment if approved
    if review['deployment']['status'] == "approved":
        print("\n📦 Generating Kubernetes deployment...")
        
        deployment_config = {
            "app_name": "user-service",
            "image": "myregistry/user-service:v1.0.0",
            "replicas": 3,
            "expose_externally": True,
            "domain": "api.example.com"
        }
        
        deployment = await pipeline.generate_deployment(review, deployment_config)
        
        print(f"\nDeployment Status: {deployment['status']}")
        
        if deployment['status'] == "ready":
            print("\n📄 Generated Manifests:")
            for manifest_type in deployment['manifests']:
                print(f"  - {manifest_type}.yaml")
            
            print("\n🔧 Kubectl Commands:")
            for cmd in deployment['kubectl_commands'][:5]:
                print(f"  {cmd}")


async def custom_review_team():
    """Example with custom review team configuration."""
    print("\n" + "="*50)
    print("Custom Review Team Example")
    print("="*50 + "\n")
    
    # Create pipeline with custom configuration
    pipeline = CodeReviewPipeline(
        name="SecurityFocusedPipeline",
        mode=ReviewMode.THOROUGH,
        agents_per_file=5,  # Use all 5 reviewers
        model="gpt-4",  # Use a specific model
        provider="openai"  # Use a specific provider
    )
    
    # Security-sensitive code
    secure_code = '''
import jwt
import bcrypt
from datetime import datetime, timedelta
import secrets

class AuthService:
    """Secure authentication service."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self, user_id: int) -> str:
        """Generate JWT token."""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
'''
    
    # Review with custom team
    print("🔍 Reviewing with custom security-focused team...")
    review = await pipeline.review(secure_code, language="python")
    
    # Show which reviewers were involved
    print("\n👥 Review Team:")
    for agent in review['pipeline_reasoning']['agents_used']:
        print(f"  - {agent}")
    
    print(f"\n✅ Security Score: {review['aggregated']['average_score']:.1f}/100")
    
    # Show any security-specific feedback
    security_issues = [
        issue for issue in review['aggregated']['all_issues']
        if issue.get('type') == 'security'
    ]
    
    if security_issues:
        print(f"\n🔒 Security Issues Found: {len(security_issues)}")
    else:
        print("\n🔒 No security issues found - code follows security best practices!")


async def main():
    """Run all examples."""
    print("\n🚀 AgentiCraft Code Review Pipeline Examples")
    print("=" * 60)
    
    # Run examples
    await basic_code_review()
    await github_pr_review()
    await deployment_generation()
    await custom_review_team()
    
    print("\n✅ All examples completed!")
    print("\n💡 Tips:")
    print("- Use 'quick' mode for rapid feedback during development")
    print("- Use 'standard' mode for regular code reviews")
    print("- Use 'thorough' mode for critical code and security reviews")
    print("- Configure GitHub integration for automated PR reviews")
    print("- Generate Kubernetes manifests after successful reviews")


if __name__ == "__main__":
    asyncio.run(main())
