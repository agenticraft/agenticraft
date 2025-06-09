"""AgentiCraft Marketplace - Plugin registry and distribution.

This module provides the infrastructure for discovering, installing,
and managing plugins in the AgentiCraft ecosystem.
"""

from .manifest import (
    AGENT_MANIFEST_TEMPLATE,
    TOOL_MANIFEST_TEMPLATE,
    PluginAuthor,
    PluginCategory,
    PluginConfig,
    PluginDependency,
    PluginEndpoint,
    PluginLicense,
    PluginManifest,
    PluginRequirements,
    PluginType,
    create_manifest,
)
from .registry import (
    PluginInfo,
    RegistryClient,
    RegistryConfig,
    SearchResult,
    install_plugin,
    list_installed_plugins,
    search_plugins,
)
from .version import (
    Version,
    VersionConflict,
    VersionRange,
    check_compatibility,
    resolve_version,
)

__all__ = [
    # Manifest
    "PluginManifest",
    "PluginType",
    "PluginCategory",
    "PluginLicense",
    "PluginAuthor",
    "PluginDependency",
    "PluginRequirements",
    "PluginConfig",
    "PluginEndpoint",
    "create_manifest",
    "TOOL_MANIFEST_TEMPLATE",
    "AGENT_MANIFEST_TEMPLATE",
    # Registry
    "RegistryClient",
    "RegistryConfig",
    "SearchResult",
    "PluginInfo",
    "search_plugins",
    "install_plugin",
    "list_installed_plugins",
    # Version
    "Version",
    "VersionRange",
    "VersionConflict",
    "resolve_version",
    "check_compatibility",
]
