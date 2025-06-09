"""Tests for version management."""

import pytest

from agenticraft.marketplace.version import (
    Version,
    VersionConflict,
    VersionRange,
    check_compatibility,
    resolve_version,
)


def test_version_parsing():
    """Test version string parsing."""
    # Basic version
    v = Version("1.2.3")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3
    assert v.prerelease is None
    assert v.build is None

    # Version with prerelease
    v = Version("2.0.0-beta.1")
    assert v.major == 2
    assert v.minor == 0
    assert v.patch == 0
    assert v.prerelease == "beta.1"

    # Version with build metadata
    v = Version("1.0.0+build.123")
    assert v.build == "build.123"

    # Version with both
    v = Version("3.1.4-rc.2+build.456")
    assert v.major == 3
    assert v.minor == 1
    assert v.patch == 4
    assert v.prerelease == "rc.2"
    assert v.build == "build.456"

    # Invalid versions
    with pytest.raises(ValueError):
        Version("1.2")  # Missing patch

    with pytest.raises(ValueError):
        Version("1.2.3.4")  # Too many parts

    with pytest.raises(ValueError):
        Version("v1.2.3")  # Invalid prefix


def test_version_string_conversion():
    """Test converting version to string."""
    assert str(Version("1.2.3")) == "1.2.3"
    assert str(Version("2.0.0-alpha")) == "2.0.0-alpha"
    assert str(Version("1.0.0+build")) == "1.0.0+build"
    assert str(Version("3.0.0-beta.1+build.2")) == "3.0.0-beta.1+build.2"


def test_version_comparison():
    """Test version comparison operations."""
    v1 = Version("1.0.0")
    v2 = Version("1.0.1")
    v3 = Version("1.1.0")
    v4 = Version("2.0.0")

    # Less than
    assert v1 < v2
    assert v2 < v3
    assert v3 < v4

    # Greater than
    assert v4 > v3
    assert v3 > v2
    assert v2 > v1

    # Equal
    assert v1 == Version("1.0.0")
    assert v1 != v2

    # Less than or equal
    assert v1 <= v2
    assert v1 <= Version("1.0.0")

    # Greater than or equal
    assert v2 >= v1
    assert v2 >= Version("1.0.1")


def test_version_prerelease_comparison():
    """Test prerelease version comparison."""
    stable = Version("1.0.0")
    alpha = Version("1.0.0-alpha")
    beta = Version("1.0.0-beta")
    rc = Version("1.0.0-rc.1")
    rc2 = Version("1.0.0-rc.2")

    # Prerelease < stable
    assert alpha < stable
    assert beta < stable
    assert rc < stable

    # Prerelease ordering
    assert alpha < beta  # Alphabetical
    assert beta < rc
    assert rc < rc2  # Numeric comparison in prerelease

    # Complex prerelease
    assert Version("1.0.0-alpha.1") < Version("1.0.0-alpha.2")
    assert Version("1.0.0-1") < Version("1.0.0-2")
    assert Version("1.0.0-a.1") < Version("1.0.0-a.2")


def test_version_bump_methods():
    """Test version bumping methods."""
    v = Version("1.2.3")

    # Bump major
    v_major = v.bump_major()
    assert str(v_major) == "2.0.0"

    # Bump minor
    v_minor = v.bump_minor()
    assert str(v_minor) == "1.3.0"

    # Bump patch
    v_patch = v.bump_patch()
    assert str(v_patch) == "1.2.4"

    # Original unchanged
    assert str(v) == "1.2.3"


def test_version_compatibility():
    """Test version compatibility checking."""
    v1 = Version("1.2.3")
    v2 = Version("1.3.0")
    v3 = Version("2.0.0")

    # Same major version = compatible
    assert v2.is_compatible_with(v1)  # 1.3.0 compatible with 1.2.3
    assert not v1.is_compatible_with(v2)  # 1.2.3 not compatible with 1.3.0 (older)

    # Different major version = not compatible
    assert not v3.is_compatible_with(v1)
    assert not v1.is_compatible_with(v3)


def test_version_range_parsing():
    """Test version range specification parsing."""
    # Valid ranges
    ranges = [
        VersionRange(spec="*"),
        VersionRange(spec="=1.2.3"),
        VersionRange(spec=">1.0.0"),
        VersionRange(spec=">=2.0.0"),
        VersionRange(spec="<3.0.0"),
        VersionRange(spec="<=1.5.0"),
        VersionRange(spec="~1.2.3"),
        VersionRange(spec="^1.0.0"),
        VersionRange(spec="1.*"),
        VersionRange(spec="2.1.*"),
    ]

    for r in ranges:
        assert r.spec

    # Invalid ranges
    with pytest.raises(ValueError):
        VersionRange(spec="invalid")

    with pytest.raises(ValueError):
        VersionRange(spec=">>1.0.0")


def test_version_range_contains():
    """Test version range containment checking."""
    v1 = Version("1.2.3")
    v2 = Version("1.3.0")
    v3 = Version("2.0.0")

    # Any version
    assert VersionRange(spec="*").contains(v1)
    assert VersionRange(spec="*").contains(v3)

    # Exact version
    assert VersionRange(spec="=1.2.3").contains(v1)
    assert not VersionRange(spec="=1.2.3").contains(v2)

    # Greater than
    assert VersionRange(spec=">1.2.0").contains(v1)
    assert not VersionRange(spec=">1.3.0").contains(v2)

    # Greater than or equal
    assert VersionRange(spec=">=1.2.3").contains(v1)
    assert VersionRange(spec=">=1.2.3").contains(v2)

    # Less than
    assert VersionRange(spec="<2.0.0").contains(v1)
    assert not VersionRange(spec="<1.2.3").contains(v1)

    # Less than or equal
    assert VersionRange(spec="<=1.3.0").contains(v1)
    assert VersionRange(spec="<=1.3.0").contains(v2)
    assert not VersionRange(spec="<=1.3.0").contains(v3)

    # Tilde (same major.minor)
    assert VersionRange(spec="~1.2.0").contains(v1)
    assert not VersionRange(spec="~1.2.0").contains(v2)
    assert not VersionRange(spec="~1.2.0").contains(v3)

    # Caret (same major)
    assert VersionRange(spec="^1.0.0").contains(v1)
    assert VersionRange(spec="^1.0.0").contains(v2)
    assert not VersionRange(spec="^1.0.0").contains(v3)

    # Wildcards
    assert VersionRange(spec="1.*").contains(v1)
    assert VersionRange(spec="1.*").contains(v2)
    assert not VersionRange(spec="1.*").contains(v3)

    assert VersionRange(spec="1.2.*").contains(v1)
    assert not VersionRange(spec="1.2.*").contains(v2)


def test_version_satisfies():
    """Test version satisfies method."""
    v = Version("1.5.2")

    assert v.satisfies(VersionRange(spec=">=1.0.0"))
    assert v.satisfies(VersionRange(spec="^1.0.0"))
    assert v.satisfies(VersionRange(spec="~1.5.0"))
    assert not v.satisfies(VersionRange(spec="<1.5.0"))
    assert not v.satisfies(VersionRange(spec="^2.0.0"))


def test_resolve_version():
    """Test version resolution from available versions."""
    available = ["1.0.0", "1.2.3", "1.2.4", "1.3.0", "2.0.0", "2.1.0"]

    # Get latest matching version
    assert resolve_version(available, "*") == "2.1.0"
    assert resolve_version(available, ">=1.0.0") == "2.1.0"
    assert resolve_version(available, "^1.0.0") == "1.3.0"
    assert resolve_version(available, "~1.2.0") == "1.2.4"
    assert resolve_version(available, "=1.2.3") == "1.2.3"
    assert resolve_version(available, ">1.2.3") == "2.1.0"
    assert resolve_version(available, "1.*") == "1.3.0"

    # No match
    assert resolve_version(available, "=3.0.0") is None
    assert resolve_version(available, ">3.0.0") is None

    # Handle invalid versions in list
    available_with_invalid = available + ["invalid", "1.2", ""]
    assert resolve_version(available_with_invalid, "^2.0.0") == "2.1.0"


def test_check_compatibility():
    """Test checking compatibility of dependencies."""
    # No conflicts
    deps = [
        ("requests", ">=2.28.0", "2.30.0"),
        ("numpy", "^1.20.0", "1.24.0"),
        ("pandas", "~2.0.0", "2.0.3"),
    ]

    conflicts = check_compatibility(deps)
    assert len(conflicts) == 0

    # With conflicts
    deps_with_conflicts = [
        ("requests", ">=3.0.0", "2.30.0"),  # Conflict
        ("numpy", "^2.0.0", "1.24.0"),  # Conflict
        ("pandas", "~2.0.0", "2.0.3"),  # OK
    ]

    conflicts = check_compatibility(deps_with_conflicts)
    assert len(conflicts) == 2

    # Check conflict details
    conflict_packages = [c.package for c in conflicts]
    assert "requests" in conflict_packages
    assert "numpy" in conflict_packages

    # Multiple requirements for same package
    deps_multi = [
        ("requests", ">=2.0.0", "2.30.0"),
        ("requests", "<3.0.0", "2.30.0"),
        ("requests", "!=2.29.0", "2.30.0"),
    ]

    conflicts = check_compatibility(deps_multi)
    assert len(conflicts) == 0  # All requirements satisfied

    # Conflicting multiple requirements
    deps_multi_conflict = [
        ("requests", ">=2.0.0", "1.0.0"),
        ("requests", "<3.0.0", "1.0.0"),
    ]

    conflicts = check_compatibility(deps_multi_conflict)
    assert len(conflicts) >= 1  # At least one requirement fails


def test_version_conflict_exception():
    """Test VersionConflict exception."""
    conflict = VersionConflict(
        package="requests", required=">=3.0.0", installed="2.30.0"
    )

    assert conflict.package == "requests"
    assert conflict.required == ">=3.0.0"
    assert conflict.installed == "2.30.0"
    assert "requests" in str(conflict)
    assert ">=3.0.0" in str(conflict)
    assert "2.30.0" in str(conflict)


def test_version_hash_and_equality():
    """Test version hashing and equality for use in sets/dicts."""
    v1 = Version("1.2.3")
    v2 = Version("1.2.3")
    v3 = Version("1.2.4")

    # Equal versions have same hash
    assert hash(v1) == hash(v2)
    assert v1 == v2

    # Different versions have different hashes (usually)
    assert v1 != v3

    # Can be used in sets
    version_set = {v1, v2, v3}
    assert len(version_set) == 2  # v1 and v2 are same

    # Can be used as dict keys
    version_dict = {v1: "first", v3: "second"}
    assert version_dict[v2] == "first"  # v2 equals v1
