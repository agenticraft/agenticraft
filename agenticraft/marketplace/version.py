"""Version management for plugins.

This module provides semantic versioning support for plugin
version management and dependency resolution.
"""

import re

from pydantic import BaseModel, field_validator


class Version(BaseModel):
    """Semantic version representation.

    Follows Semantic Versioning 2.0.0 specification.
    """

    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    build: str | None = None

    def __init__(self, version_string: str = None, **kwargs):
        """Initialize from string or components."""
        if version_string:
            parsed = self._parse_version(version_string)
            super().__init__(**parsed)
        else:
            super().__init__(**kwargs)

    @staticmethod
    def _parse_version(version_string: str) -> dict:
        """Parse version string."""
        # Regex for semantic version
        pattern = (
            r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-.]+))?(?:\+([a-zA-Z0-9\-.]+))?$"
        )
        match = re.match(pattern, version_string)

        if not match:
            raise ValueError(f"Invalid version string: {version_string}")

        major, minor, patch, prerelease, build = match.groups()

        return {
            "major": int(major),
            "minor": int(minor),
            "patch": int(patch),
            "prerelease": prerelease,
            "build": build,
        }

    def __str__(self) -> str:
        """Convert to string representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"

        if self.prerelease:
            version += f"-{self.prerelease}"

        if self.build:
            version += f"+{self.build}"

        return version

    def __eq__(self, other: "Version") -> bool:
        """Check equality."""
        if not isinstance(other, Version):
            return False

        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __lt__(self, other: "Version") -> bool:
        """Check if less than other version."""
        if not isinstance(other, Version):
            return NotImplemented

        # Compare major, minor, patch
        if self.major != other.major:
            return self.major < other.major

        if self.minor != other.minor:
            return self.minor < other.minor

        if self.patch != other.patch:
            return self.patch < other.patch

        # Handle prerelease versions
        if self.prerelease and not other.prerelease:
            return True  # Prerelease < release
        elif not self.prerelease and other.prerelease:
            return False  # Release > prerelease
        elif self.prerelease and other.prerelease:
            # Compare prerelease identifiers
            return self._compare_prerelease(self.prerelease, other.prerelease)

        return False

    def __le__(self, other: "Version") -> bool:
        """Check if less than or equal."""
        return self == other or self < other

    def __gt__(self, other: "Version") -> bool:
        """Check if greater than."""
        return not self <= other

    def __ge__(self, other: "Version") -> bool:
        """Check if greater than or equal."""
        return not self < other

    def __hash__(self) -> int:
        """Get hash for use in sets/dicts."""
        return hash((self.major, self.minor, self.patch, self.prerelease))

    @staticmethod
    def _compare_prerelease(pre1: str, pre2: str) -> bool:
        """Compare prerelease versions."""
        # Split by dots
        parts1 = pre1.split(".")
        parts2 = pre2.split(".")

        for i in range(max(len(parts1), len(parts2))):
            # Get parts or None
            p1 = parts1[i] if i < len(parts1) else None
            p2 = parts2[i] if i < len(parts2) else None

            # Missing parts come first
            if p1 is None:
                return True
            elif p2 is None:
                return False

            # Try numeric comparison
            try:
                n1, n2 = int(p1), int(p2)
                if n1 != n2:
                    return n1 < n2
            except ValueError:
                # String comparison
                if p1 != p2:
                    return p1 < p2

        return False

    def bump_major(self) -> "Version":
        """Bump major version."""
        return Version(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> "Version":
        """Bump minor version."""
        return Version(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> "Version":
        """Bump patch version."""
        return Version(major=self.major, minor=self.minor, patch=self.patch + 1)

    def is_compatible_with(self, other: "Version") -> bool:
        """Check if compatible with another version (same major)."""
        return self.major == other.major and self >= other

    def satisfies(self, spec: "VersionRange") -> bool:
        """Check if version satisfies a version range."""
        return spec.contains(self)


class VersionRange(BaseModel):
    """Version range specification."""

    spec: str

    @field_validator("spec")
    def validate_spec(cls, v: str) -> str:
        """Validate version specification."""
        # Support common patterns
        patterns = [
            r"^\*$",  # Any version
            r"^=(\d+\.\d+\.\d+.*)$",  # Exact version
            r"^!=(\d+\.\d+\.\d+.*)$",  # Not equal to
            r"^>(\d+\.\d+\.\d+.*)$",  # Greater than
            r"^>=(\d+\.\d+\.\d+.*)$",  # Greater than or equal
            r"^<(\d+\.\d+\.\d+.*)$",  # Less than
            r"^<=(\d+\.\d+\.\d+.*)$",  # Less than or equal
            r"^~(\d+\.\d+\.\d+.*)$",  # Compatible with (same major.minor)
            r"^\^(\d+\.\d+\.\d+.*)$",  # Compatible with (same major)
            r"^(\d+\.\d+\.\*)$",  # Minor version wildcard
            r"^(\d+\.\*)$",  # Major version wildcard
        ]

        if not any(re.match(pattern, v) for pattern in patterns):
            raise ValueError(f"Invalid version specification: {v}")

        return v

    def contains(self, version: Version) -> bool:
        """Check if version is within range."""
        spec = self.spec.strip()

        # Any version
        if spec == "*":
            return True

        # Not equal to
        if spec.startswith("!="):
            target = Version(spec[2:])
            return version != target

        # Exact version
        if spec.startswith("="):
            target = Version(spec[1:])
            return version == target

        # Greater than or equal
        if spec.startswith(">="):
            target = Version(spec[2:])
            return version >= target

        # Greater than
        if spec.startswith(">"):
            target = Version(spec[1:])
            return version > target

        # Less than or equal
        if spec.startswith("<="):
            target = Version(spec[2:])
            return version <= target

        # Less than
        if spec.startswith("<"):
            target = Version(spec[1:])
            return version < target

        # Compatible with (tilde)
        if spec.startswith("~"):
            target = Version(spec[1:])
            return (
                version.major == target.major
                and version.minor == target.minor
                and version >= target
            )

        # Compatible with (caret)
        if spec.startswith("^"):
            target = Version(spec[1:])
            return version.is_compatible_with(target)

        # Wildcard versions
        if spec.endswith(".*"):
            parts = spec[:-2].split(".")
            if len(parts) == 1:
                # Major version wildcard
                return version.major == int(parts[0])
            elif len(parts) == 2:
                # Minor version wildcard
                return version.major == int(parts[0]) and version.minor == int(parts[1])

        # Try as exact version
        try:
            target = Version(spec)
            return version == target
        except ValueError:
            return False

    def __str__(self) -> str:
        """String representation."""
        return self.spec


class VersionConflict(Exception):
    """Version conflict error."""

    def __init__(self, package: str, required: str, installed: str):
        self.package = package
        self.required = required
        self.installed = installed

        super().__init__(
            f"Version conflict for {package}: "
            f"required {required}, installed {installed}"
        )


def resolve_version(available_versions: list[str], requirement: str) -> str | None:
    """Resolve the best version from available versions.

    Args:
        available_versions: List of available version strings
        requirement: Version requirement specification

    Returns:
        Best matching version or None
    """
    # Parse versions
    versions = []
    for v in available_versions:
        try:
            versions.append(Version(v))
        except ValueError:
            continue

    # Sort versions (newest first)
    versions.sort(reverse=True)

    # Create version range
    version_range = VersionRange(spec=requirement)

    # Find best match
    for version in versions:
        if version_range.contains(version):
            return str(version)

    return None


def check_compatibility(
    dependencies: list[tuple[str, str, str]],
) -> list[VersionConflict]:
    """Check for version conflicts in dependencies.

    Args:
        dependencies: List of (package, required_version, installed_version)

    Returns:
        List of version conflicts
    """
    conflicts = []

    # Group by package
    package_requirements = {}
    for package, required, installed in dependencies:
        if package not in package_requirements:
            package_requirements[package] = {"requirements": [], "installed": installed}
        package_requirements[package]["requirements"].append(required)

    # Check each package
    for package, info in package_requirements.items():
        installed = info["installed"]

        if installed:
            installed_version = Version(installed)

            # Check all requirements
            for req in info["requirements"]:
                version_range = VersionRange(spec=req)
                if not version_range.contains(installed_version):
                    conflicts.append(VersionConflict(package, req, installed))

    return conflicts


# Example usage
if __name__ == "__main__":
    # Version examples
    v1 = Version("1.2.3")
    v2 = Version("1.2.4")
    v3 = Version("2.0.0")
    v4 = Version("1.2.3-alpha.1")

    print(f"{v1} < {v2}: {v1 < v2}")
    print(f"{v2} < {v3}: {v2 < v3}")
    print(f"{v4} < {v1}: {v4 < v1}")

    # Version range examples
    range1 = VersionRange(spec=">=1.2.0")
    range2 = VersionRange(spec="~1.2.3")
    range3 = VersionRange(spec="^1.0.0")

    print(f"\n{v1} satisfies {range1}: {v1.satisfies(range1)}")
    print(f"{v3} satisfies {range2}: {v3.satisfies(range2)}")
    print(f"{v2} satisfies {range3}: {v2.satisfies(range3)}")

    # Resolution example
    available = ["1.0.0", "1.2.3", "1.2.4", "2.0.0", "2.1.0"]
    best = resolve_version(available, "^1.2.0")
    print(f"\nBest version for ^1.2.0: {best}")
