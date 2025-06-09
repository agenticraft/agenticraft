# Registry Setup Guide

Guide to hosting your own AgentiCraft plugin registry for private or organizational use.

## Overview

A plugin registry allows you to:
- Host private plugins within your organization
- Control plugin distribution and access
- Implement custom authentication and authorization
- Track usage and analytics
- Enforce security policies

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Clients   │────▶│ Registry API │────▶│  Storage    │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Auth      │     │  Database   │
                    └──────────────┘     └─────────────┘
```

## Quick Setup

### Using Docker

```bash
# Clone registry template
git clone https://github.com/agenticraft/registry-template
cd registry-template

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start registry
docker-compose up -d

# Registry available at http://localhost:8080
```

### Manual Setup

```bash
# Install registry server
pip install agenticraft-registry-server

# Initialize registry
agenticraft-registry init

# Start server
agenticraft-registry serve --host 0.0.0.0 --port 8080
```

## Registry Implementation

### Basic Registry Server

```python
# registry_server.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from typing import List, Optional
import uvicorn

from agenticraft.marketplace import (
    PluginManifest,
    PluginInfo,
    Version
)

app = FastAPI(title="AgentiCraft Plugin Registry")
security = HTTPBearer()

# Database setup
engine = create_engine("postgresql://user:pass@localhost/registry")

# Storage backend
storage = S3Storage(bucket="agenticraft-plugins")

@app.get("/")
async def root():
    """Registry information."""
    return {
        "name": "My AgentiCraft Registry",
        "version": "1.0.0",
        "plugins_count": await get_plugin_count()
    }

@app.get("/api/v1/plugins")
async def search_plugins(
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0
) -> List[PluginInfo]:
    """Search for plugins."""
    return await search_registry(
        query=query,
        tags=tags,
        limit=limit,
        offset=offset
    )

@app.get("/api/v1/plugins/{name}")
async def get_plugin(
    name: str,
    version: Optional[str] = None
) -> PluginInfo:
    """Get plugin information."""
    plugin = await fetch_plugin(name, version)
    if not plugin:
        raise HTTPException(404, "Plugin not found")
    return plugin

@app.post("/api/v1/plugins")
async def publish_plugin(
    manifest: UploadFile,
    package: UploadFile,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Publish a new plugin."""
    # Authenticate
    user = await authenticate(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid authentication")
    
    # Validate manifest
    manifest_data = await manifest.read()
    plugin_manifest = PluginManifest.parse_raw(manifest_data)
    
    # Check permissions
    if not can_publish(user, plugin_manifest.name):
        raise HTTPException(403, "Permission denied")
    
    # Store plugin
    await store_plugin(plugin_manifest, package)
    
    return {
        "success": True,
        "plugin": plugin_manifest.name,
        "version": plugin_manifest.version
    }

@app.get("/api/v1/plugins/{name}/download")
async def download_plugin(
    name: str,
    version: str
) -> str:
    """Get plugin download URL."""
    url = await get_download_url(name, version)
    if not url:
        raise HTTPException(404, "Plugin version not found")
    return {"download_url": url}
```

### Database Schema

```python
# models.py
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Plugin(Base):
    __tablename__ = "plugins"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    author = Column(String)
    license = Column(String)
    homepage = Column(String)
    repository = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relationships
    versions = relationship("PluginVersion", back_populates="plugin")
    tags = relationship("PluginTag", back_populates="plugin")

class PluginVersion(Base):
    __tablename__ = "plugin_versions"
    
    id = Column(Integer, primary_key=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"))
    version = Column(String)
    manifest = Column(JSON)
    package_url = Column(String)
    downloads = Column(Integer, default=0)
    published_at = Column(DateTime)
    published_by = Column(String)
    
    # Relationships
    plugin = relationship("Plugin", back_populates="versions")

class PluginTag(Base):
    __tablename__ = "plugin_tags"
    
    id = Column(Integer, primary_key=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"))
    tag = Column(String, index=True)
    
    # Relationships
    plugin = relationship("Plugin", back_populates="tags")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    api_token = Column(String, unique=True)
    permissions = Column(JSON)
    created_at = Column(DateTime)
```

### Storage Backend

```python
# storage.py
from abc import ABC, abstractmethod
import boto3
from pathlib import Path
from typing import BinaryIO

class StorageBackend(ABC):
    """Abstract storage backend."""
    
    @abstractmethod
    async def store(self, key: str, file: BinaryIO) -> str:
        """Store a file and return URL."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> bytes:
        """Retrieve file contents."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a file."""
        pass

class S3Storage(StorageBackend):
    """AWS S3 storage backend."""
    
    def __init__(self, bucket: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region)
    
    async def store(self, key: str, file: BinaryIO) -> str:
        """Store file in S3."""
        self.s3.upload_fileobj(file, self.bucket, key)
        return f"https://{self.bucket}.s3.amazonaws.com/{key}"
    
    async def retrieve(self, key: str) -> bytes:
        """Retrieve from S3."""
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()
    
    async def delete(self, key: str) -> None:
        """Delete from S3."""
        self.s3.delete_object(Bucket=self.bucket, Key=key)

class LocalStorage(StorageBackend):
    """Local filesystem storage."""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def store(self, key: str, file: BinaryIO) -> str:
        """Store file locally."""
        path = self.base_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            f.write(file.read())
        
        return f"file://{path.absolute()}"
    
    async def retrieve(self, key: str) -> bytes:
        """Retrieve from filesystem."""
        path = self.base_path / key
        return path.read_bytes()
    
    async def delete(self, key: str) -> None:
        """Delete from filesystem."""
        path = self.base_path / key
        path.unlink(missing_ok=True)
```

### Authentication & Authorization

```python
# auth.py
from typing import Optional, List
import jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt

class AuthManager:
    """Handle authentication and authorization."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_token(self, user_id: int, username: str) -> str:
        """Create JWT token."""
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode token."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password."""
        return bcrypt.hash(password)
    
    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password."""
        return bcrypt.verify(password, hash)

class PermissionManager:
    """Handle permissions."""
    
    PERMISSIONS = {
        "admin": ["*"],
        "publisher": ["publish", "update", "delete_own"],
        "user": ["read", "download"]
    }
    
    def __init__(self):
        self.role_permissions = self.PERMISSIONS.copy()
    
    def has_permission(
        self,
        user: dict,
        action: str,
        resource: Optional[str] = None
    ) -> bool:
        """Check if user has permission."""
        user_role = user.get("role", "user")
        permissions = self.role_permissions.get(user_role, [])
        
        # Admin has all permissions
        if "*" in permissions:
            return True
        
        # Check specific permission
        if action in permissions:
            return True
        
        # Check resource-specific permissions
        if resource and f"{action}:{resource}" in permissions:
            return True
        
        # Check own resources
        if action.endswith("_own") and resource:
            return self._is_owner(user, resource)
        
        return False
    
    def _is_owner(self, user: dict, resource: str) -> bool:
        """Check if user owns resource."""
        # Implementation depends on your data model
        pass
```

### API Authentication

```python
# api_auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user."""
    token = credentials.credentials
    
    # Verify token
    auth_manager = AuthManager(settings.SECRET_KEY)
    payload = auth_manager.verify_token(token)
    
    if not payload:
        raise HTTPException(401, "Invalid authentication")
    
    # Get user from database
    user = await get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(401, "User not found")
    
    return user

async def require_permission(permission: str):
    """Require specific permission."""
    async def check_permission(
        user: dict = Depends(get_current_user)
    ) -> dict:
        perm_manager = PermissionManager()
        if not perm_manager.has_permission(user, permission):
            raise HTTPException(403, "Permission denied")
        return user
    
    return check_permission

# Usage in endpoints
@app.post("/api/v1/plugins")
async def publish_plugin(
    manifest: UploadFile,
    package: UploadFile,
    user: dict = Depends(require_permission("publish"))
):
    """Publish plugin (requires publish permission)."""
    # Implementation
    pass
```

## Advanced Features

### Plugin Validation

```python
# validation.py
from typing import List, Tuple
import tempfile
import zipfile
import subprocess

class PluginValidator:
    """Validate plugin packages."""
    
    async def validate_package(
        self,
        package_path: Path
    ) -> Tuple[bool, List[str]]:
        """Validate plugin package."""
        errors = []
        
        # Extract package
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with zipfile.ZipFile(package_path, "r") as zf:
                    zf.extractall(tmpdir)
            except Exception as e:
                errors.append(f"Invalid package format: {e}")
                return False, errors
            
            # Check structure
            tmppath = Path(tmpdir)
            
            # Manifest must exist
            manifest_path = tmppath / "plugin.yaml"
            if not manifest_path.exists():
                errors.append("Missing plugin.yaml")
            else:
                # Validate manifest
                try:
                    manifest = PluginManifest.load(manifest_path)
                    manifest_errors = manifest.validate()
                    errors.extend(manifest_errors)
                except Exception as e:
                    errors.append(f"Invalid manifest: {e}")
            
            # Check required files
            required_files = ["README.md", "LICENSE"]
            for file in required_files:
                if not (tmppath / file).exists():
                    errors.append(f"Missing required file: {file}")
            
            # Run tests if present
            if (tmppath / "tests").exists():
                result = subprocess.run(
                    ["pytest", str(tmppath / "tests")],
                    capture_output=True
                )
                if result.returncode != 0:
                    errors.append("Tests failed")
            
            # Security scan
            security_errors = await self._security_scan(tmppath)
            errors.extend(security_errors)
        
        return len(errors) == 0, errors
    
    async def _security_scan(self, path: Path) -> List[str]:
        """Scan for security issues."""
        errors = []
        
        # Check for dangerous imports
        dangerous_imports = [
            "os.system",
            "subprocess.run",
            "exec(",
            "eval(",
            "__import__"
        ]
        
        for py_file in path.rglob("*.py"):
            content = py_file.read_text()
            for dangerous in dangerous_imports:
                if dangerous in content:
                    errors.append(
                        f"Potentially dangerous code in {py_file}: {dangerous}"
                    )
        
        return errors
```

### Analytics & Metrics

```python
# analytics.py
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio

class AnalyticsCollector:
    """Collect registry analytics."""
    
    def __init__(self, database):
        self.db = database
    
    async def track_download(
        self,
        plugin_name: str,
        version: str,
        user_id: Optional[int] = None
    ):
        """Track plugin download."""
        await self.db.execute(
            """
            INSERT INTO downloads 
            (plugin_name, version, user_id, timestamp, ip_address)
            VALUES ($1, $2, $3, $4, $5)
            """,
            plugin_name, version, user_id, 
            datetime.utcnow(), request.client.host
        )
    
    async def track_search(
        self,
        query: str,
        results_count: int,
        user_id: Optional[int] = None
    ):
        """Track search queries."""
        await self.db.execute(
            """
            INSERT INTO searches
            (query, results_count, user_id, timestamp)
            VALUES ($1, $2, $3, $4)
            """,
            query, results_count, user_id, datetime.utcnow()
        )
    
    async def get_popular_plugins(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict]:
        """Get most popular plugins."""
        since = datetime.utcnow() - timedelta(days=days)
        
        return await self.db.fetch_all(
            """
            SELECT 
                plugin_name,
                COUNT(*) as download_count
            FROM downloads
            WHERE timestamp > $1
            GROUP BY plugin_name
            ORDER BY download_count DESC
            LIMIT $2
            """,
            since, limit
        )
    
    async def get_metrics(self) -> Dict:
        """Get registry metrics."""
        return {
            "total_plugins": await self._count_plugins(),
            "total_downloads": await self._count_downloads(),
            "active_users": await self._count_active_users(),
            "popular_plugins": await self.get_popular_plugins(),
            "recent_publishes": await self._get_recent_publishes()
        }
```

### CDN Integration

```python
# cdn.py
import cloudflare

class CDNManager:
    """Manage CDN distribution."""
    
    def __init__(self, cf_config: dict):
        self.cf = cloudflare.CloudFlare(
            email=cf_config["email"],
            key=cf_config["api_key"]
        )
        self.zone_id = cf_config["zone_id"]
    
    async def purge_cache(self, plugin_name: str, version: str):
        """Purge CDN cache for plugin."""
        urls = [
            f"https://registry.example.com/plugins/{plugin_name}/{version}/*"
        ]
        
        self.cf.zones.purge_cache.post(
            self.zone_id,
            data={"files": urls}
        )
    
    async def configure_caching(self):
        """Configure CDN caching rules."""
        # Cache plugin packages for 1 year
        self.cf.page_rules.post(
            self.zone_id,
            data={
                "targets": [{
                    "target": "url",
                    "constraint": {
                        "operator": "matches",
                        "value": "*/plugins/*/*.tar.gz"
                    }
                }],
                "actions": [{
                    "id": "browser_cache_ttl",
                    "value": 31536000  # 1 year
                }]
            }
        )
```

## Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 registry && \
    chown -R registry:registry /app

USER registry

# Run server
CMD ["uvicorn", "registry_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  registry:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/registry
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=registry
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - registry
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
# registry-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agenticraft-registry
spec:
  replicas: 3
  selector:
    matchLabels:
      app: registry
  template:
    metadata:
      labels:
        app: registry
    spec:
      containers:
      - name: registry
        image: agenticraft/registry:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: registry-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: registry-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: registry-service
spec:
  selector:
    app: registry
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

## Security

### Security Checklist

- [ ] HTTPS only with valid certificates
- [ ] API authentication required
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CORS properly configured
- [ ] Security headers set
- [ ] Regular security audits
- [ ] Dependency scanning
- [ ] Container scanning
- [ ] Secrets management

### Security Configuration

```python
# security.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["registry.example.com", "*.example.com"]
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

## Monitoring

### Health Checks

```python
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Readiness check with dependencies."""
    checks = {
        "database": await check_database(),
        "storage": await check_storage(),
        "cache": await check_cache()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        {"status": "ready" if all_healthy else "not ready", "checks": checks},
        status_code=status_code
    )

async def check_database() -> bool:
    """Check database connectivity."""
    try:
        await db.execute("SELECT 1")
        return True
    except:
        return False
```

### Metrics

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
plugin_downloads = Counter(
    'registry_plugin_downloads_total',
    'Total plugin downloads',
    ['plugin', 'version']
)

api_requests = Histogram(
    'registry_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status']
)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")
```

## Next Steps

- [Plugin Development](plugin-development.md) - Create plugins
- [Marketplace Guide](README.md) - Using the marketplace
- [API Reference](api-reference.md) - Complete API docs
- [Examples](../../examples/marketplace/) - Working examples
