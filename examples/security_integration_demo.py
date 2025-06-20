"""
Example showing how to integrate authentication and authorization
with AgentiCraft agents and workflows.
"""
import asyncio
from typing import Dict, Any

from agenticraft import Agent, Workflow
from agenticraft.workflows import ResearchTeam
from agenticraft.security import (
    security,
    UserContext,
    AuthenticationError,
    AuthorizationError
)


# Example 1: Secure Agent with Authentication
class SecureAgent(Agent):
    """Agent that requires authentication for execution."""
    
    async def execute(self, task: str, user_context: UserContext = None, **kwargs) -> Any:
        """Execute task with security checks."""
        if not user_context:
            raise AuthenticationError("Authentication required")
            
        # Check permission
        if not await security.authorize(user_context, "agent", "execute"):
            raise AuthorizationError("Not authorized to execute agents")
            
        # Log execution start
        async with security.audit_logger.audit_context(
            user_id=user_context.user_id,
            username=user_context.username,
            action="execute",
            resource=f"agent:{self.name}"
        ) as audit:
            # Execute task
            result = await super().execute(task, **kwargs)
            
            # Add audit details
            audit["task"] = task[:100]  # First 100 chars
            audit["success"] = True
            
            return result


# Example 2: Secure Workflow with RBAC
class SecureWorkflow(Workflow):
    """Workflow that enforces role-based access control."""
    
    def __init__(self, name: str, required_role: str = "user", **kwargs):
        super().__init__(name, **kwargs)
        self.required_role = required_role
        
    async def execute(self, task: str, user_context: UserContext = None, **kwargs) -> Any:
        """Execute workflow with RBAC checks."""
        if not user_context:
            raise AuthenticationError("Authentication required")
            
        # Check role
        if not user_context.has_role(self.required_role):
            raise AuthorizationError(
                f"Role '{self.required_role}' required for workflow '{self.name}'"
            )
            
        # Check permission
        if not await security.authorize(user_context, "workflow", "execute"):
            raise AuthorizationError("Not authorized to execute workflows")
            
        # Execute with audit
        return await super().execute(task, **kwargs)


# Example 3: API Endpoint with Security Decorator
@security.secure_endpoint("agent", "create")
async def create_agent_endpoint(
    request: Dict[str, Any],
    user_context: UserContext,  # Automatically injected
    agent_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a new agent (requires authentication and authorization)."""
    # user_context is automatically validated and injected
    
    # Create agent
    agent = Agent(
        name=agent_config["name"],
        model=agent_config.get("model", "gpt-4"),
        sandbox_enabled=True  # Always enable sandbox for security
    )
    
    # Return response
    return {
        "success": True,
        "agent_id": agent.id,
        "created_by": user_context.username
    }


# Example 4: Using Multiple Permissions
@security.require_permissions("agent:execute", "sandbox:execute")
async def execute_sandboxed_code(
    user_context: UserContext,
    code: str
) -> Dict[str, Any]:
    """Execute code in sandbox (requires multiple permissions)."""
    # Create sandboxed agent
    agent = Agent(
        name="code-executor",
        sandbox_enabled=True,
        sandbox_type="docker"
    )
    
    # Execute code
    result = await agent.execute_secure(code, user_context=user_context)
    
    return {
        "success": result.success,
        "output": result.result,
        "execution_time_ms": result.execution_time_ms
    }


# Example 5: Complete Secure Research Workflow
async def secure_research_example():
    """Example of using authentication with research workflow."""
    
    # Step 1: Create API key for user
    api_key = await security.create_api_key(
        user_id="researcher_001",
        username="jane_researcher",
        roles=["researcher", "user"],
        permissions=["workflow:execute", "agent:execute"],
        expires_in_days=30
    )
    
    print(f"API Key created: {api_key[:20]}...")
    
    # Step 2: Simulate authenticated request
    request = {
        "headers": {
            "X-API-Key": api_key,
            "User-Agent": "AgentiCraft-Client/1.0"
        },
        "ip_address": "192.168.1.100"
    }
    
    # Step 3: Authenticate
    user_context = await security.authenticate(request)
    if not user_context:
        raise AuthenticationError("Failed to authenticate")
        
    print(f"Authenticated as: {user_context.username}")
    
    # Step 4: Create secure research team
    research_team = ResearchTeam(
        size=3,
        coordination_mode="hybrid",
        sandbox_type="process"  # Use process sandbox for performance
    )
    
    # Step 5: Execute research with security context
    async with security.audit_logger.audit_context(
        user_id=user_context.user_id,
        username=user_context.username,
        action="execute",
        resource="research_team"
    ) as audit:
        # Check authorization
        if not await security.authorize(user_context, "workflow", "execute"):
            raise AuthorizationError("Not authorized to execute workflows")
            
        # Execute research
        research_topic = "Latest developments in quantum computing security"
        result = await research_team.execute(research_topic)
        
        # Add audit details
        audit["topic"] = research_topic
        audit["agent_count"] = len(research_team.agents)
        audit["coordination_mode"] = "hybrid"
        
    print(f"Research completed. Report length: {len(str(result))} chars")
    
    # Step 6: Check user activity
    activity = await security.get_user_activity(user_context.user_id, days=1)
    print(f"User activity: {activity['total_events']} events in last day")
    
    # Step 7: Detect anomalies
    anomalies = await security.detect_anomalies(user_context.user_id)
    if anomalies:
        print(f"Anomalies detected: {anomalies}")


# Example 6: JWT Authentication Flow
async def jwt_authentication_example():
    """Example of JWT-based authentication."""
    
    # Step 1: User logs in (normally would verify credentials)
    user_context = UserContext(
        user_id="user_123",
        username="john_doe",
        email="john@example.com",
        roles=["developer", "user"],
        permissions=["agent:*", "workflow:*"]
    )
    
    # Step 2: Create JWT tokens
    access_token, refresh_token = await security.create_jwt_tokens(user_context)
    print(f"Access token: {access_token[:50]}...")
    print(f"Refresh token: {refresh_token[:50]}...")
    
    # Step 3: Use access token for API calls
    request = {
        "headers": {
            "Authorization": f"Bearer {access_token}"
        }
    }
    
    # Step 4: Authenticate with JWT
    authenticated_user = await security.authenticate(request)
    print(f"JWT authenticated as: {authenticated_user.username}")
    
    # Step 5: When access token expires, refresh it
    try:
        # This would normally happen when token is expired
        jwt_provider = security.auth_providers[AuthMethod.JWT]
        new_access_token = await jwt_provider.refresh_access_token(refresh_token)
        print(f"New access token: {new_access_token[:50]}...")
    except Exception as e:
        print(f"Token refresh error: {e}")


# Example 7: Admin Operations
async def admin_operations_example():
    """Example of administrative security operations."""
    
    # Create admin user
    admin_key = await security.create_api_key(
        user_id="admin_001",
        username="admin",
        roles=["admin"],
        permissions=["*:*"],  # All permissions
        expires_in_days=7  # Short-lived for security
    )
    
    # Authenticate as admin
    admin_context = await security.authenticate({
        "headers": {"X-API-Key": admin_key}
    })
    
    # Perform admin operations
    
    # 1. Create new role
    security.authorizer.create_role(
        "ml_engineer",
        "Machine Learning Engineer with model access",
        permissions=[
            "agent:*",
            "workflow:*",
            "model:*",
            "sandbox:execute"
        ]
    )
    
    # 2. Assign role to user
    security.authorizer.assign_role("user_456", "ml_engineer")
    
    # 3. Query audit logs
    recent_events = await security.audit_logger.query_logs(
        limit=10,
        event_type=AuditEventType.AGENT_EXECUTED
    )
    
    print(f"Recent agent executions: {len(recent_events)}")
    
    # 4. Monitor suspicious activity
    for user_id in ["user_123", "user_456"]:
        anomalies = await security.detect_anomalies(user_id)
        if anomalies:
            print(f"User {user_id} anomalies: {anomalies}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(secure_research_example())
    # asyncio.run(jwt_authentication_example())
    # asyncio.run(admin_operations_example())
