"""Registry client for AgentiCraft marketplace.

This module provides the client for interacting with the plugin registry,
including search, install, update, and publish functionality.
"""

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field, HttpUrl

from .manifest import PluginCategory, PluginManifest, PluginType
from .version import Version

logger = logging.getLogger(__name__)


class RegistryConfig(BaseModel):
    """Configuration for registry client."""

    registry_url: HttpUrl = Field(
        default="https://registry.agenticraft.ai",
        description="Base URL of the plugin registry",
    )
    api_version: str = "v1"
    timeout: int = 30
    max_retries: int = 3
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".agenticraft" / "cache"
    )
    plugins_dir: Path = Field(
        default_factory=lambda: Path.home() / ".agenticraft" / "plugins"
    )
    api_key: str | None = Field(
        default=None, description="API key for authenticated operations"
    )


class SearchResult(BaseModel):
    """A search result from the registry."""

    name: str
    version: str
    type: PluginType
    title: str
    description: str
    author: str
    downloads: int
    rating: float | None
    verified: bool

    def to_display_string(self) -> str:
        """Format for display."""
        stars = "★" * int(self.rating or 0) if self.rating else "No rating"
        verified_badge = "✓" if self.verified else ""

        return (
            f"{self.name} ({self.version}) {verified_badge}\n"
            f"  {self.title}\n"
            f"  {self.description}\n"
            f"  By: {self.author} | Downloads: {self.downloads} | {stars}"
        )


class PluginInfo(BaseModel):
    """Detailed plugin information from registry."""

    manifest: PluginManifest
    versions: list[str]
    latest_version: str
    total_downloads: int
    dependencies_graph: dict[str, list[str]] = Field(default_factory=dict)
    readme: str | None = None
    changelog: str | None = None


class RegistryClient:
    """Client for interacting with the AgentiCraft plugin registry.

    This client provides methods for searching, installing, updating,
    and publishing plugins to the marketplace.

    Args:
        config: Registry configuration

    Example:
        Basic usage::

            client = RegistryClient()

            # Search for plugins
            results = await client.search("web browser")

            # Install a plugin
            await client.install("web-browser-tool")

            # List installed plugins
            installed = await client.list_installed()
    """

    def __init__(self, config: RegistryConfig | None = None):
        """Initialize registry client."""
        self.config = config or RegistryConfig()

        # Create directories
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self.config.plugins_dir.mkdir(parents=True, exist_ok=True)

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout, headers=self._get_headers()
        )

        # Local registry cache
        self.cache_file = self.config.cache_dir / "registry_cache.json"
        self._cache = self._load_cache()

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers."""
        headers = {
            "User-Agent": "AgentiCraft-Registry-Client/1.0",
            "Accept": "application/json",
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    def _load_cache(self) -> dict[str, Any]:
        """Load local registry cache."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

        return {"plugins": {}, "updated_at": None}

    def _save_cache(self) -> None:
        """Save local registry cache."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _get_api_url(self, endpoint: str) -> str:
        """Build API URL."""
        base = f"{self.config.registry_url}/api/{self.config.api_version}"
        return urljoin(base + "/", endpoint.lstrip("/"))

    async def search(
        self,
        query: str,
        plugin_type: PluginType | None = None,
        category: PluginCategory | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search for plugins in the registry.

        Args:
            query: Search query
            plugin_type: Filter by plugin type
            category: Filter by category
            limit: Maximum results

        Returns:
            List of search results
        """
        params = {"q": query, "limit": limit}

        if plugin_type:
            params["type"] = plugin_type
        if category:
            params["category"] = category

        try:
            response = await self.client.get(self._get_api_url("search"), params=params)
            response.raise_for_status()

            data = response.json()
            return [SearchResult(**item) for item in data["results"]]

        except Exception as e:
            logger.error(f"Search failed: {e}")

            # Fallback to cache
            return self._search_cache(query, plugin_type, category, limit)

    def _search_cache(
        self,
        query: str,
        plugin_type: PluginType | None = None,
        category: PluginCategory | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search in local cache."""
        results = []
        query_lower = query.lower()

        for plugin_name, plugin_data in self._cache.get("plugins", {}).items():
            # Filter by type and category
            if plugin_type and plugin_data.get("type") != plugin_type:
                continue
            if category and plugin_data.get("category") != category:
                continue

            # Simple text search
            search_text = plugin_data.get("search_text", "").lower()
            if query_lower in search_text:
                results.append(SearchResult(**plugin_data))

                if len(results) >= limit:
                    break

        return results

    async def get_plugin_info(self, name: str) -> PluginInfo | None:
        """Get detailed information about a plugin.

        Args:
            name: Plugin name

        Returns:
            Plugin information or None if not found
        """
        try:
            response = await self.client.get(self._get_api_url(f"plugins/{name}"))
            response.raise_for_status()

            data = response.json()
            manifest = PluginManifest(**data["manifest"])

            return PluginInfo(
                manifest=manifest,
                versions=data.get("versions", []),
                latest_version=data.get("latest_version", manifest.version),
                total_downloads=data.get("total_downloads", 0),
                dependencies_graph=data.get("dependencies_graph", {}),
                readme=data.get("readme"),
                changelog=data.get("changelog"),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"Plugin not found: {name}")
            else:
                logger.error(f"Failed to get plugin info: {e}")
            return None

        except Exception as e:
            logger.error(f"Failed to get plugin info: {e}")
            return None

    async def install(
        self,
        name: str,
        version: str | None = None,
        upgrade: bool = False,
        force: bool = False,
    ) -> bool:
        """Install a plugin from the registry.

        Args:
            name: Plugin name
            version: Specific version (latest if None)
            upgrade: Upgrade if already installed
            force: Force reinstall

        Returns:
            True if successful
        """
        # Check if already installed
        installed_path = self.config.plugins_dir / name
        if installed_path.exists() and not (upgrade or force):
            logger.info(f"Plugin already installed: {name}")
            return True

        # Get plugin info
        info = await self.get_plugin_info(name)
        if not info:
            return False

        # Resolve version
        target_version = version or info.latest_version
        if target_version not in info.versions:
            logger.error(f"Version not found: {target_version}")
            return False

        # Check dependencies
        if not await self._check_dependencies(info.manifest):
            return False

        # Download plugin
        download_url = self._get_api_url(f"plugins/{name}/download/{target_version}")

        try:
            logger.info(f"Downloading {name} v{target_version}...")

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / f"{name}.tar.gz"

                # Download archive
                async with self.client.stream("GET", download_url) as response:
                    response.raise_for_status()

                    with open(temp_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)

                # Extract to plugins directory
                import tarfile

                with tarfile.open(temp_path, "r:gz") as tar:
                    tar.extractall(self.config.plugins_dir)

                # Save manifest
                manifest_path = installed_path / "plugin.yaml"
                manifest_path.write_text(info.manifest.to_yaml())

                # Update cache
                self._cache["plugins"][name] = info.manifest.to_registry_format()
                self._save_cache()

                logger.info(f"Successfully installed {name} v{target_version}")
                return True

        except Exception as e:
            logger.error(f"Installation failed: {e}")

            # Cleanup on failure
            if installed_path.exists():
                shutil.rmtree(installed_path)

            return False

    async def _check_dependencies(self, manifest: PluginManifest) -> bool:
        """Check if dependencies are satisfied."""
        # Check Python version
        import sys

        from packaging import specifiers

        python_spec = specifiers.SpecifierSet(manifest.requirements.python)
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        if python_version not in python_spec:
            logger.error(
                f"Python version mismatch: requires {manifest.requirements.python}, "
                f"have {python_version}"
            )
            return False

        # Check AgentiCraft version
        try:
            import agenticraft

            ac_version = getattr(agenticraft, "__version__", "0.0.0")
            ac_spec = specifiers.SpecifierSet(manifest.requirements.agenticraft)

            if ac_version not in ac_spec:
                logger.error(
                    f"AgentiCraft version mismatch: requires {manifest.requirements.agenticraft}, "
                    f"have {ac_version}"
                )
                return False

        except ImportError:
            logger.error("AgentiCraft not installed")
            return False

        # Check other dependencies
        for dep in manifest.requirements.dependencies:
            if not dep.optional:
                # Check if plugin dependency is installed
                dep_path = self.config.plugins_dir / dep.name
                if not dep_path.exists():
                    logger.info(f"Installing dependency: {dep.name}")
                    if not await self.install(dep.name, dep.version):
                        return False

        return True

    async def uninstall(self, name: str) -> bool:
        """Uninstall a plugin.

        Args:
            name: Plugin name

        Returns:
            True if successful
        """
        plugin_path = self.config.plugins_dir / name

        if not plugin_path.exists():
            logger.error(f"Plugin not installed: {name}")
            return False

        try:
            # Remove from filesystem
            shutil.rmtree(plugin_path)

            # Update cache
            if name in self._cache.get("plugins", {}):
                del self._cache["plugins"][name]
                self._save_cache()

            logger.info(f"Successfully uninstalled {name}")
            return True

        except Exception as e:
            logger.error(f"Uninstall failed: {e}")
            return False

    async def list_installed(self) -> list[PluginManifest]:
        """List installed plugins.

        Returns:
            List of installed plugin manifests
        """
        installed = []

        for plugin_dir in self.config.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_path = plugin_dir / "plugin.yaml"
                if manifest_path.exists():
                    try:
                        manifest = PluginManifest.from_yaml(manifest_path.read_text())
                        installed.append(manifest)
                    except Exception as e:
                        logger.warning(
                            f"Failed to load manifest for {plugin_dir.name}: {e}"
                        )

        return installed

    async def update(self, name: str | None = None) -> list[str]:
        """Update installed plugins.

        Args:
            name: Specific plugin to update (all if None)

        Returns:
            List of updated plugins
        """
        updated = []

        if name:
            # Update specific plugin
            if await self._update_plugin(name):
                updated.append(name)
        else:
            # Update all plugins
            installed = await self.list_installed()
            for manifest in installed:
                if await self._update_plugin(manifest.name):
                    updated.append(manifest.name)

        return updated

    async def _update_plugin(self, name: str) -> bool:
        """Update a single plugin."""
        # Get current version
        plugin_path = self.config.plugins_dir / name
        manifest_path = plugin_path / "plugin.yaml"

        if not manifest_path.exists():
            return False

        try:
            current_manifest = PluginManifest.from_yaml(manifest_path.read_text())
            current_version = Version(current_manifest.version)

            # Get latest version from registry
            info = await self.get_plugin_info(name)
            if not info:
                return False

            latest_version = Version(info.latest_version)

            # Check if update available
            if latest_version > current_version:
                logger.info(
                    f"Updating {name} from {current_version} to {latest_version}"
                )
                return await self.install(name, str(latest_version), upgrade=True)
            else:
                logger.info(f"{name} is up to date")
                return False

        except Exception as e:
            logger.error(f"Failed to update {name}: {e}")
            return False

    async def publish(self, manifest_path: str | Path, package_dir: str | Path) -> bool:
        """Publish a plugin to the registry.

        Args:
            manifest_path: Path to plugin.yaml
            package_dir: Directory containing plugin code

        Returns:
            True if successful
        """
        if not self.config.api_key:
            logger.error("API key required for publishing")
            return False

        manifest_path = Path(manifest_path)
        package_dir = Path(package_dir)

        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return False

        if not package_dir.exists():
            logger.error(f"Package directory not found: {package_dir}")
            return False

        try:
            # Load manifest
            manifest = PluginManifest.from_yaml(manifest_path.read_text())

            # Create package archive
            with tempfile.NamedTemporaryFile(suffix=".tar.gz") as temp_file:
                import tarfile

                with tarfile.open(temp_file.name, "w:gz") as tar:
                    tar.add(package_dir, arcname=manifest.name)
                    tar.add(manifest_path, arcname=f"{manifest.name}/plugin.yaml")

                # Upload to registry
                files = {
                    "package": ("package.tar.gz", open(temp_file.name, "rb")),
                    "manifest": ("plugin.yaml", manifest.to_yaml()),
                }

                response = await self.client.post(
                    self._get_api_url("plugins/publish"), files=files
                )
                response.raise_for_status()

                logger.info(
                    f"Successfully published {manifest.name} v{manifest.version}"
                )
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Publish failed: {e.response.text}")
            return False

        except Exception as e:
            logger.error(f"Publish failed: {e}")
            return False

    async def refresh_cache(self) -> None:
        """Refresh the local registry cache."""
        try:
            response = await self.client.get(self._get_api_url("plugins/all"))
            response.raise_for_status()

            data = response.json()
            self._cache = {
                "plugins": {p["name"]: p for p in data["plugins"]},
                "updated_at": data.get("updated_at"),
            }
            self._save_cache()

            logger.info("Registry cache refreshed")

        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")

    async def close(self) -> None:
        """Close the client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience functions


async def search_plugins(
    query: str, plugin_type: PluginType | None = None, limit: int = 10
) -> list[SearchResult]:
    """Quick search for plugins.

    Args:
        query: Search query
        plugin_type: Filter by type
        limit: Maximum results

    Returns:
        Search results
    """
    async with RegistryClient() as client:
        return await client.search(query, plugin_type=plugin_type, limit=limit)


async def install_plugin(name: str, version: str | None = None) -> bool:
    """Quick install a plugin.

    Args:
        name: Plugin name
        version: Optional version

    Returns:
        True if successful
    """
    async with RegistryClient() as client:
        return await client.install(name, version)


async def list_installed_plugins() -> list[PluginManifest]:
    """Quick list installed plugins.

    Returns:
        List of installed plugins
    """
    async with RegistryClient() as client:
        return await client.list_installed()
