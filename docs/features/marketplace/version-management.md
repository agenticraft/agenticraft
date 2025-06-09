# Version Management Guide

Comprehensive guide to version management in AgentiCraft's Tool Marketplace using semantic versioning.

## Overview

AgentiCraft uses Semantic Versioning 2.0.0 (semver) for all plugins. This ensures:
- Clear communication of changes
- Predictable dependency resolution
- Backward compatibility guarantees
- Automated update strategies

## Semantic Versioning

### Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

Examples:
1.0.0           - First stable release
1.2.3           - Standard version
2.0.0-alpha     - Alpha pre-release
2.0.0-beta.1    - Beta pre-release
2.0.0-rc.1      - Release candidate
1.0.0+20250615  - Version with build metadata
```

### Version Components

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality
- **PATCH**: Backward-compatible bug fixes
- **PRERELEASE**: Optional pre-release identifier
- **BUILD**: Optional build metadata

## Version Class

### Basic Usage

```python
from agenticraft.marketplace import Version

# Create versions
v1 = Version("1.2.3")
v2 = Version("2.0.0-beta.1")
v3 = Version("1.2.4")

# Compare versions
print(v1 < v2)      # True
print(v1 < v3)      # True
print(v2.is_prerelease)  # True

# Version components
print(v1.major)     # 1
print(v1.minor)     # 2
print(v1.patch)     # 3
```

### Advanced Features

```python
# Parse complex versions
v = Version("2.1.0-alpha.1+build.123")
print(v.prerelease)    # ['alpha', 1]
print(v.build)         # ['build', '123']

# Version incrementing
v = Version("1.2.3")
print(v.bump_major())  # 2.0.0
print(v.bump_minor())  # 1.3.0
print(v.bump_patch())  # 1.2.4

# Pre-release progression
v = Version("1.0.0-alpha")
print(v.bump_prerelease())  # 1.0.0-alpha.1
```

## Version Ranges

### Range Specifications

```python
from agenticraft.marketplace import VersionRange

# Caret ranges (^) - Compatible versions
r1 = VersionRange("^1.2.3")
# Allows: 1.2.3, 1.2.4, 1.3.0, 1.9.9
# Denies: 2.0.0, 1.2.2

# Tilde ranges (~) - Patch-level changes
r2 = VersionRange("~1.2.3")
# Allows: 1.2.3, 1.2.4, 1.2.9
# Denies: 1.3.0, 1.2.2

# Comparison operators
r3 = VersionRange(">=1.0.0")
r4 = VersionRange("<2.0.0")
r5 = VersionRange(">=1.0.0,<2.0.0")  # Combined

# Exact version
r6 = VersionRange("=1.2.3")
```

### Range Validation

```python
# Check if version satisfies range
v = Version("1.5.0")
r = VersionRange("^1.0.0")

print(r.allows(v))  # True

# Multiple ranges
ranges = [
    VersionRange(">=1.0.0"),
    VersionRange("<2.0.0"),
    VersionRange("!=1.5.0")
]

# Check all ranges
valid = all(r.allows(v) for r in ranges)
```

## Dependency Resolution

### Dependency Specification

```yaml
# In plugin.yaml
dependencies:
  # Caret - most common, allows compatible updates
  agenticraft: "^0.2.0"
  
  # Tilde - more restrictive
  requests: "~2.28.0"
  
  # Range - explicit boundaries
  numpy: ">=1.20.0,<2.0.0"
  
  # Exact - use sparingly
  critical-lib: "=1.0.0"
  
  # Latest - not recommended for production
  dev-tool: "*"
  
  # Pre-release
  beta-lib: "^1.0.0-beta"
```

### Resolution Algorithm

```python
from agenticraft.marketplace import DependencyResolver

# Create resolver
resolver = DependencyResolver()

# Add dependencies
resolver.add_dependency("my-plugin", "requests", "^2.28.0")
resolver.add_dependency("my-plugin", "numpy", ">=1.20.0")
resolver.add_dependency("other-plugin", "requests", "~2.28.1")

# Resolve
try:
    solution = resolver.resolve()
    print("Resolved versions:")
    for package, version in solution.items():
        print(f"  {package}: {version}")
except VersionConflict as e:
    print(f"Conflict: {e}")
```

### Conflict Detection

```python
class ConflictDetector:
    """Detect version conflicts in dependencies."""
    
    def __init__(self):
        self.dependencies = {}
    
    def add_requirement(self, package: str, version_spec: str, required_by: str):
        """Add a version requirement."""
        if package not in self.dependencies:
            self.dependencies[package] = []
        
        self.dependencies[package].append({
            "spec": VersionRange(version_spec),
            "required_by": required_by
        })
    
    def find_conflicts(self):
        """Find all version conflicts."""
        conflicts = []
        
        for package, requirements in self.dependencies.items():
            # Check if requirements are compatible
            if not self._are_compatible(requirements):
                conflicts.append({
                    "package": package,
                    "requirements": requirements
                })
        
        return conflicts
    
    def _are_compatible(self, requirements):
        """Check if all requirements can be satisfied."""
        # Find intersection of all version ranges
        allowed_versions = None
        
        for req in requirements:
            if allowed_versions is None:
                allowed_versions = req["spec"]
            else:
                # Intersect ranges
                allowed_versions = allowed_versions.intersect(req["spec"])
                if allowed_versions.is_empty():
                    return False
        
        return True
```

## Version Strategies

### Release Strategies

```python
class ReleaseStrategy:
    """Different version release strategies."""
    
    @staticmethod
    def stable_release(current: Version) -> Version:
        """Standard stable release."""
        if current.is_prerelease:
            # Remove pre-release
            return Version(f"{current.major}.{current.minor}.{current.patch}")
        else:
            # Bump patch
            return current.bump_patch()
    
    @staticmethod
    def feature_release(current: Version) -> Version:
        """New feature release."""
        return current.bump_minor()
    
    @staticmethod
    def breaking_release(current: Version) -> Version:
        """Breaking change release."""
        return current.bump_major()
    
    @staticmethod
    def prerelease_cycle(current: Version, stage: str = "alpha") -> Version:
        """Pre-release cycle progression."""
        base = f"{current.major}.{current.minor}.{current.patch}"
        
        if not current.is_prerelease:
            # Start pre-release
            return Version(f"{base}-{stage}")
        elif stage in str(current):
            # Increment current stage
            return current.bump_prerelease()
        else:
            # Move to new stage
            return Version(f"{base}-{stage}")
```

### Update Policies

```python
from enum import Enum

class UpdatePolicy(Enum):
    """Plugin update policies."""
    CONSERVATIVE = "conservative"  # Only patch updates
    BALANCED = "balanced"          # Minor updates
    AGGRESSIVE = "aggressive"      # Major updates
    MANUAL = "manual"             # No automatic updates

class UpdateManager:
    """Manage plugin updates based on policy."""
    
    def __init__(self, policy: UpdatePolicy = UpdatePolicy.BALANCED):
        self.policy = policy
    
    def should_update(self, current: Version, available: Version) -> bool:
        """Check if update should be applied."""
        if self.policy == UpdatePolicy.MANUAL:
            return False
        
        if available.is_prerelease and not current.is_prerelease:
            return False  # Don't auto-update to pre-release
        
        if self.policy == UpdatePolicy.CONSERVATIVE:
            # Only patch updates
            return (current.major == available.major and
                   current.minor == available.minor and
                   current.patch < available.patch)
        
        elif self.policy == UpdatePolicy.BALANCED:
            # Minor updates
            return (current.major == available.major and
                   current < available)
        
        elif self.policy == UpdatePolicy.AGGRESSIVE:
            # Any newer version
            return current < available
        
        return False
    
    def get_update_range(self, current: Version) -> str:
        """Get version range for updates."""
        if self.policy == UpdatePolicy.CONSERVATIVE:
            return f"~{current}"
        elif self.policy == UpdatePolicy.BALANCED:
            return f"^{current}"
        elif self.policy == UpdatePolicy.AGGRESSIVE:
            return f">={current}"
        else:
            return f"={current}"
```

## Version Lifecycle

### Pre-release Progression

```python
class PrereleaseManager:
    """Manage pre-release versioning."""
    
    STAGES = ["dev", "alpha", "beta", "rc"]
    
    @classmethod
    def next_prerelease(cls, current: Version) -> Version:
        """Get next pre-release version."""
        if not current.is_prerelease:
            # Start with dev
            return Version(f"{current}-dev")
        
        # Parse current stage
        prerelease_str = str(current.prerelease[0])
        
        for i, stage in enumerate(cls.STAGES):
            if stage in prerelease_str:
                if i < len(cls.STAGES) - 1:
                    # Move to next stage
                    next_stage = cls.STAGES[i + 1]
                    base = f"{current.major}.{current.minor}.{current.patch}"
                    return Version(f"{base}-{next_stage}")
                else:
                    # At RC, next is stable
                    return Version(f"{current.major}.{current.minor}.{current.patch}")
        
        # Increment current pre-release
        return current.bump_prerelease()
    
    @classmethod
    def is_ready_for_stable(cls, version: Version) -> bool:
        """Check if ready for stable release."""
        if not version.is_prerelease:
            return False
        
        # Must be at RC stage
        return "rc" in str(version.prerelease[0])
```

### Version History

```python
from datetime import datetime
from typing import List, Dict

class VersionHistory:
    """Track version history and changes."""
    
    def __init__(self):
        self.releases = []
    
    def add_release(
        self,
        version: Version,
        changes: Dict[str, List[str]],
        release_date: datetime = None
    ):
        """Add a release to history."""
        self.releases.append({
            "version": version,
            "date": release_date or datetime.now(),
            "changes": changes
        })
    
    def get_changelog(self, from_version: Version = None) -> str:
        """Generate changelog."""
        changelog = ["# Changelog\n"]
        
        for release in sorted(self.releases, key=lambda r: r["version"], reverse=True):
            if from_version and release["version"] <= from_version:
                break
            
            version = release["version"]
            date = release["date"].strftime("%Y-%m-%d")
            changelog.append(f"\n## [{version}] - {date}\n")
            
            for category, items in release["changes"].items():
                if items:
                    changelog.append(f"\n### {category}")
                    for item in items:
                        changelog.append(f"- {item}")
        
        return "\n".join(changelog)
    
    def get_version_type(self, version: Version) -> str:
        """Determine version type from history."""
        if not self.releases:
            return "initial"
        
        previous = self.releases[-1]["version"]
        
        if version.major > previous.major:
            return "major"
        elif version.minor > previous.minor:
            return "minor"
        elif version.patch > previous.patch:
            return "patch"
        elif version.is_prerelease:
            return "prerelease"
        else:
            return "unknown"
```

## Best Practices

### 1. Version Incrementing

```python
def determine_version_bump(changes: List[str]) -> str:
    """Determine version bump type from changes."""
    # Keywords indicating breaking changes
    breaking_keywords = ["BREAKING", "removed", "changed API"]
    feature_keywords = ["added", "new feature", "enhancement"]
    
    for change in changes:
        if any(keyword in change for keyword in breaking_keywords):
            return "major"
    
    for change in changes:
        if any(keyword in change for keyword in feature_keywords):
            return "minor"
    
    return "patch"
```

### 2. Dependency Specification

```yaml
# Good practices
dependencies:
  # Use caret for most dependencies
  agenticraft: "^0.2.0"
  
  # Use tilde for more stability
  critical-lib: "~1.0.0"
  
  # Be specific about major versions
  breaking-lib: ">=2.0.0,<3.0.0"

# Avoid
dependencies:
  # Too restrictive
  some-lib: "=1.2.3"
  
  # Too permissive
  another-lib: "*"
  
  # No version spec
  unversioned-lib: ""
```

### 3. Pre-release Guidelines

```python
# Pre-release naming convention
class PrereleaseNaming:
    @staticmethod
    def create_prerelease(base_version: str, stage: str, number: int = None):
        """Create consistent pre-release versions."""
        if number is None:
            return f"{base_version}-{stage}"
        else:
            return f"{base_version}-{stage}.{number}"
    
    # Examples:
    # 1.0.0-dev        # Development
    # 1.0.0-alpha      # Alpha
    # 1.0.0-alpha.1    # Alpha iteration
    # 1.0.0-beta       # Beta
    # 1.0.0-beta.2     # Beta iteration
    # 1.0.0-rc         # Release candidate
    # 1.0.0-rc.1       # RC iteration
```

## Automation

### Version Bumping Script

```python
#!/usr/bin/env python3
# scripts/bump_version.py

import argparse
import re
from pathlib import Path
from agenticraft.marketplace import Version

def bump_version(bump_type: str, prerelease: str = None):
    """Bump version in all files."""
    # Read current version
    manifest_path = Path("plugin.yaml")
    content = manifest_path.read_text()
    
    # Extract current version
    match = re.search(r"version: ([^\n]+)", content)
    if not match:
        raise ValueError("Version not found in manifest")
    
    current = Version(match.group(1))
    
    # Determine new version
    if bump_type == "major":
        new_version = current.bump_major()
    elif bump_type == "minor":
        new_version = current.bump_minor()
    elif bump_type == "patch":
        new_version = current.bump_patch()
    elif bump_type == "prerelease":
        if prerelease:
            base = f"{current.major}.{current.minor}.{current.patch}"
            new_version = Version(f"{base}-{prerelease}")
        else:
            new_version = current.bump_prerelease()
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")
    
    print(f"Bumping version: {current} → {new_version}")
    
    # Update files
    files_to_update = [
        "plugin.yaml",
        "setup.py",
        "src/*/__init__.py"
    ]
    
    for pattern in files_to_update:
        for file_path in Path(".").glob(pattern):
            if file_path.is_file():
                update_version_in_file(file_path, str(current), str(new_version))
    
    return new_version

def update_version_in_file(file_path: Path, old_version: str, new_version: str):
    """Update version in a single file."""
    content = file_path.read_text()
    updated = content.replace(old_version, new_version)
    
    if updated != content:
        file_path.write_text(updated)
        print(f"  Updated {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bump plugin version")
    parser.add_argument("type", choices=["major", "minor", "patch", "prerelease"])
    parser.add_argument("--prerelease", help="Pre-release identifier")
    
    args = parser.parse_args()
    new_version = bump_version(args.type, args.prerelease)
    
    print(f"\nNew version: {new_version}")
    print("\nDon't forget to:")
    print("1. Update CHANGELOG.md")
    print("2. Commit changes")
    print("3. Create git tag")
```

### CI/CD Integration

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Parse version
        id: version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          
          # Check if pre-release
          if [[ $VERSION =~ -(alpha|beta|rc) ]]; then
            echo "prerelease=true" >> $GITHUB_OUTPUT
          else
            echo "prerelease=false" >> $GITHUB_OUTPUT
          fi
      
      - name: Validate version
        run: |
          python -c "
          from agenticraft.marketplace import Version
          v = Version('${{ steps.version.outputs.version }}')
          print(f'Valid version: {v}')
          "
      
      - name: Build plugin
        run: |
          pip install build
          python -m build
      
      - name: Publish to marketplace
        env:
          MARKETPLACE_TOKEN: ${{ secrets.MARKETPLACE_TOKEN }}
        run: |
          agenticraft plugin publish \
            --version ${{ steps.version.outputs.version }} \
            --prerelease ${{ steps.version.outputs.prerelease }}
```

## Troubleshooting

### Common Issues

**Version conflict errors**:
```python
# Debug version conflicts
from agenticraft.marketplace import debug_version_conflict

debug_version_conflict("package-name")
```

**Invalid version format**:
```python
# Validate version string
try:
    v = Version("1.2.3.4")  # Invalid
except ValueError as e:
    print(f"Invalid version: {e}")
```

**Range parsing errors**:
```python
# Test version ranges
from agenticraft.marketplace import test_version_range

test_version_range("^1.0.0", ["1.0.0", "1.1.0", "2.0.0"])
```

## Next Steps

- [Plugin Development](plugin-development.md) - Create plugins
- [Registry Setup](registry-setup.md) - Host your own registry
- [API Reference](api-reference.md) - Complete API documentation
- [Examples](../../examples/marketplace/) - Working examples
