"""
Authentication Example - Refactored Architecture

This example demonstrates various authentication methods
using the new unified auth system.
"""
import asyncio
import logging
from datetime import timedelta

from agenticraft.fabric import AgentBuilder
from agenticraft.core.auth import (
    AuthConfig, 
    AuthManager,
    get_auth_manager
)
from agenticraft.core.transport import TransportConfig

# Enable logging
logging.basicConfig(level=logging.INFO)


async def demo_bearer_auth():
    """Demonstrate Bearer token authentication."""
    print("\n=== Bearer Token Authentication ===")
    
    agent = await (AgentBuilder("bearer-agent")
        .with_mcp(
            url="http://localhost:8080",
            auth=AuthConfig.bearer("my-secret-token")
        )
        .build_and_start())
    
    try:
        # The auth headers are automatically included
        result = await agent.call("tools/list")
        print(f"Authenticated call result: {result}")
        
        # Get auth headers being used
        transport = agent.get_transport("mcp")
        if hasattr(transport, 'auth'):
            headers = transport.auth.get_headers()
            print(f"Auth headers: {headers}")
            
    finally:
        await agent.stop()


async def demo_api_key_auth():
    """Demonstrate API key authentication."""
    print("\n=== API Key Authentication ===")
    
    agent = await (AgentBuilder("apikey-agent")
        .with_mcp(
            url="http://localhost:8080",
            auth=AuthConfig.api_key(
                key="sk_test_123456789",
                header="X-API-Key"
            )
        )
        .build_and_start())
    
    try:
        result = await agent.call("tools/list")
        print(f"API key authenticated: {result}")
        
    finally:
        await agent.stop()


async def demo_jwt_auth():
    """Demonstrate JWT authentication."""
    print("\n=== JWT Authentication ===")
    
    # In real usage, you'd get the token from an auth server
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    agent = await (AgentBuilder("jwt-agent")
        .with_mcp(
            url="http://localhost:8080",
            auth=AuthConfig.jwt(
                token=jwt_token,
                secret="your-secret-key",
                algorithm="HS256"
            )
        )
        .build_and_start())
    
    try:
        result = await agent.call("tools/list")
        print(f"JWT authenticated: {result}")
        
    finally:
        await agent.stop()


async def demo_hmac_auth():
    """Demonstrate HMAC signature authentication."""
    print("\n=== HMAC Authentication ===")
    
    agent = await (AgentBuilder("hmac-agent")
        .with_mcp(
            url="http://localhost:8080",
            auth=AuthConfig.hmac(
                key_id="client-123",
                secret_key="shared-secret-key",
                algorithm="sha256"
            )
        )
        .build_and_start())
    
    try:
        # HMAC signs each request
        result = await agent.call("tools/list")
        print(f"HMAC authenticated: {result}")
        
    finally:
        await agent.stop()


async def demo_multi_auth():
    """Demonstrate multiple auth methods in one agent."""
    print("\n=== Multi-Protocol Authentication ===")
    
    agent = await (AgentBuilder("multi-auth-agent")
        # MCP with Bearer auth
        .with_mcp(
            url="http://localhost:8080",
            auth=AuthConfig.bearer("mcp-token")
        )
        # A2A with API key auth
        .with_a2a(
            pattern="mesh",
            auth=AuthConfig.api_key("a2a-key", "X-A2A-Key")
        )
        .build_and_start())
    
    try:
        # Each protocol uses its own auth
        print("MCP call (Bearer auth):")
        mcp_result = await agent.call("tools/list", protocol="mcp")
        print(f"Result: {mcp_result}")
        
        print("\nA2A call (API key auth):")
        a2a_result = await agent.send(
            {"type": "ping"},
            protocol="a2a"
        )
        print(f"Result: {a2a_result}")
        
    finally:
        await agent.stop()


async def demo_auth_manager():
    """Demonstrate direct auth manager usage."""
    print("\n=== Auth Manager Usage ===")
    
    # Get global auth manager
    auth_manager = get_auth_manager()
    
    # Create different auth configurations
    configs = [
        AuthConfig.none(),
        AuthConfig.bearer("token123"),
        AuthConfig.api_key("key456", "X-Custom-Key"),
        AuthConfig.basic("user", "pass")
    ]
    
    for config in configs:
        # Set auth configuration
        auth_manager.set_auth(config)
        
        # Get auth provider
        provider = auth_manager.get_provider()
        
        if provider:
            # Get headers
            headers = provider.get_headers()
            print(f"\nAuth type: {config.type.value}")
            print(f"Headers: {headers}")
            
            # Test authentication
            context = {"headers": headers}
            result = await provider.authenticate(context)
            print(f"Auth result: {result}")


async def demo_custom_auth():
    """Demonstrate custom authentication provider."""
    print("\n=== Custom Authentication ===")
    
    from agenticraft.core.auth import AuthProvider, AuthType
    
    # Create custom auth provider
    class TokenRotationAuthProvider(AuthProvider):
        """Auth provider that rotates tokens."""
        
        def __init__(self, config):
            super().__init__(config)
            self.tokens = config.credentials.get("tokens", [])
            self.current_index = 0
            
        async def authenticate(self, context):
            # Rotate to next token
            token = self.tokens[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.tokens)
            
            return {
                "authenticated": True,
                "token_used": token,
                "next_rotation": self.current_index
            }
            
        def get_headers(self):
            token = self.tokens[self.current_index]
            return {"Authorization": f"Bearer {token}"}
            
        def get_connection_params(self):
            return {}
    
    # Register custom provider
    auth_manager = get_auth_manager()
    auth_manager.register_provider(
        AuthType.CUSTOM,
        TokenRotationAuthProvider
    )
    
    # Use custom auth
    custom_config = AuthConfig(
        type=AuthType.CUSTOM,
        credentials={
            "tokens": ["token1", "token2", "token3"]
        }
    )
    
    agent = await (AgentBuilder("custom-auth-agent")
        .with_mcp(
            url="http://localhost:8080",
            auth=custom_config
        )
        .build_and_start())
    
    try:
        # Make multiple calls - tokens will rotate
        for i in range(5):
            result = await agent.call("tools/list")
            print(f"Call {i+1} authenticated with rotating token")
            
    finally:
        await agent.stop()


async def main():
    """Run all authentication demos."""
    
    # Run individual demos
    await demo_bearer_auth()
    await demo_api_key_auth()
    await demo_jwt_auth()
    await demo_hmac_auth()
    await demo_multi_auth()
    await demo_auth_manager()
    await demo_custom_auth()
    
    print("\n=== Authentication Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
