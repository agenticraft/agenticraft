"""Test if security module imports correctly after refactoring."""

try:
    # Test importing the security module
    from agenticraft.security import (
        SecurityContext,
        SandboxType,
        SandboxManager,
        SecurityException,
        AuthenticationError,
        AuthorizationError
    )
    
    # Test importing from core.auth directly
    from agenticraft.core.auth import (
        AuthConfig,
        AuthProvider,
        AuthManager,
        APIKeyAuthProvider,
        JWTAuthProvider
    )
    
    print("All imports successful!")
    print("\nSecurity module exports:")
    print("  - SecurityContext")
    print("  - SandboxType")
    print("  - SandboxManager")
    print("  - SecurityException")
    print("  - AuthenticationError (from core.auth)")
    print("  - AuthorizationError (from core.auth)")
    
    print("\nCore auth module exports:")
    print("  - AuthConfig")
    print("  - AuthProvider")
    print("  - AuthManager")
    print("  - APIKeyAuthProvider")
    print("  - JWTAuthProvider")
    
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
