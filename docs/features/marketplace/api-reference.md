# Marketplace API Reference

Complete API documentation for AgentiCraft's Tool Marketplace components.

## Core Classes

### PluginManifest

```python
class PluginManifest(BaseModel):
    """Plugin manifest definition.
    
    Defines all metadata, dependencies, and configuration for a plugin.
    
    Attributes:
        name (str): Plugin name (lowercase, hyphens allowed)
        version (str): Semantic version string
        description (str): Short description (max 200 chars)
        author (str): Author name and optional email
        license (str): License identifier (e.g., MIT, Apache-2.0)
        homepage (str, optional): Plugin homepage URL
        repository (str, optional): Source repository URL
        documentation (str, optional): Documentation URL
        tags (List[str], optional): Categorization tags
        tools (List[ToolDefinition]): Tools provided by plugin
        dependencies (Dict[str, str]): Required dependencies
        dev_dependencies (Dict[str, str], optional): Development dependencies
        configuration (Dict[str, ConfigOption], optional): Configuration schema
        python_requires (str, optional): Python version requirement
        entry_points (Dict[str, List[str]], optional): Plugin entry points
    
    Example:
        manifest = PluginManifest(
            name="weather-tool",
            version="1.0.0",
            description="Weather data for agents",
            author="John Doe <john@example.com>",
            license="MIT",
            tools=[...],
            dependencies={"agenticraft": ">=0.2.0"}
        )
    """
    
    name: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9-]*[a-z0-9]$",
        description="Plugin name (lowercase, hyphens)"
    )
    version: str = Field(
        ...,
        description="Semantic version"
    )
    description: str = Field(
        ...,
        max_length=200,
        description="Short description"
    )
    author: str = Field(
        ...,
        description="Author name and optional email"
    )
    license: str = Field(
        ...,
        description="License identifier"
    )
    
    # Optional metadata
    homepage: Optional[str] = None
    repository: Optional[str] = None
    documentation: Optional[str] = None
    changelog: Optional[str] = None
    
    # Categorization
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Plugin contents
    tools: List[ToolDefinition]
    dependencies: Dict[str, str] = Field(default_factory=dict)
    dev_dependencies: Dict[str, str] = Field(default_factory=dict)
    
    # Configuration
    configuration: Dict[str, ConfigOption] = Field(default_factory=dict)
    
    # Requirements
    python_requires: Optional[str] = None
    
    # Entry points
    entry_points: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Additional files
    include: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)
    
    # Scripts
    scripts: Dict[str, str] = Field(default_factory=dict)
```

#### Methods

##### validate
```python
def validate(self) -> List[str]:
    """Validate manifest completeness.
    
    Returns:
        List of validation errors (empty if valid)
        
    Example:
        errors = manifest.validate()
        if errors:
            print("Validation errors:", errors)
    """
```

##### save
```python
def save(self, path: Union[str, Path] = "plugin.yaml") -> None:
    """Save manifest to YAML file.
    
    Args:
        path: Output file path
        
    Example:
        manifest.save("plugin.yaml")
    """
```

##### load
```python
@classmethod
def load(cls, path: Union[str, Path] = "plugin.yaml") -> "PluginManifest":
    """Load manifest from YAML file.
    
    Args:
        path: Input file path
        
    Returns:
        PluginManifest instance
        
    Example:
        manifest = PluginManifest.load("plugin.yaml")
    """
```

### ToolDefinition

```python
class ToolDefinition(BaseModel):
    """Tool definition within a plugin.
    
    Attributes:
        name (str): Tool class name
        module (str): Python module path
        class_name (str): Class name (if different from name)
        description (str): Tool description
        config_schema (Dict[str, Any], optional): Tool-specific config
        
    Example:
        tool = ToolDefinition(
            name="WeatherTool",
            module="weather_tool.main",
            description="Get weather data"
        )
    """
    
    name: str = Field(..., description="Tool name")
    module: str = Field(..., description="Module path")
    class_name: Optional[str] = Field(None, description="Class name")
    description: str = Field(..., description="Tool description")
    config_schema: Optional[Dict[str, Any]] = None
    
    @property
    def import_path(self) -> str:
        """Get full import path."""
        return f"{self.module}.{self.class_name or self.name}"
```

### ConfigOption

```python
class ConfigOption(BaseModel):
    """Configuration option definition.
    
    Attributes:
        type (str): Value type (string, integer, boolean, etc.)
        description (str): Option description
        default (Any, optional): Default value
        required (bool): Whether required
        env_var (str, optional): Environment variable name
        choices (List[Any], optional): Valid choices
        minimum (Union[int, float], optional): Minimum value
        maximum (Union[int, float], optional): Maximum value
        
    Example:
        option = ConfigOption(
            type="string",
            description="API key",
            required=True,
            env_var="WEATHER_API_KEY"
        )
    """
    
    type: str = Field(..., description="Value type")
    description: str = Field(..., description="Description")
    default: Optional[Any] = None
    required: bool = Field(False, description="Is required")
    env_var: Optional[str] = None
    choices: Optional[List[Any]] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # Regex pattern for strings
    
    def validate_value(self, value: Any) -> bool:
        """Validate a configuration value."""
```

### RegistryClient

```python
class RegistryClient:
    """Client for interacting with plugin registry.
    
    Args:
        registry_url (str): Registry URL
        cache_dir (Path, optional): Local cache directory
        auth_token (str, optional): Authentication token
        timeout (int): Request timeout in seconds
        
    Example:
        registry = RegistryClient()
        results = await registry.search("weather")
    """
    
    def __init__(
        self,
        registry_url: str = "https://registry.agenticraft.com",
        cache_dir: Optional[Path] = None,
        auth_token: Optional[str] = None,
        timeout: int = 30
    ):
        self.registry_url = registry_url
        self.cache_dir = cache_dir or Path.home() / ".agenticraft" / "cache"
        self.auth_token = auth_token
        self.timeout = timeout
        self._session = None
```

#### Methods

##### search
```python
async def search(
    self,
    query: str = "",
    tags: Optional[List[str]] = None,
    author: Optional[str] = None,
    category: Optional[str] = None,
    min_version: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[PluginInfo]:
    """Search for plugins.
    
    Args:
        query: Search query
        tags: Filter by tags
        author: Filter by author
        category: Filter by category
        min_version: Minimum version
        limit: Results per page
        offset: Result offset
        
    Returns:
        List of matching plugins
        
    Example:
        results = await registry.search(
            "weather",
            tags=["api", "real-time"]
        )
    """
```

##### get_plugin
```python
async def get_plugin(
    self,
    name: str,
    version: Optional[str] = None
) -> PluginInfo:
    """Get plugin information.
    
    Args:
        name: Plugin name
        version: Specific version (latest if None)
        
    Returns:
        Plugin information
        
    Example:
        plugin = await registry.get_plugin("weather-tool")
        print(f"Latest: {plugin.latest_version}")
    """
```

##### install
```python
async def install(
    self,
    name: str,
    version: Optional[str] = None,
    force: bool = False,
    no_deps: bool = False
) -> InstalledPlugin:
    """Install a plugin.
    
    Args:
        name: Plugin name
        version: Version spec (latest if None)
        force: Force reinstall
        no_deps: Skip dependency installation
        
    Returns:
        Installed plugin info
        
    Example:
        plugin = await registry.install(
            "weather-tool",
            version="^1.0.0"
        )
    """
```

##### update
```python
async def update(
    self,
    name: str,
    version: Optional[str] = None
) -> InstalledPlugin:
    """Update a plugin.
    
    Args:
        name: Plugin name
        version: Target version (latest if None)
        
    Returns:
        Updated plugin info
        
    Example:
        updated = await registry.update("weather-tool")
    """
```

##### uninstall
```python
async def uninstall(
    self,
    name: str,
    remove_deps: bool = False
) -> None:
    """Uninstall a plugin.
    
    Args:
        name: Plugin name
        remove_deps: Also remove unused dependencies
        
    Example:
        await registry.uninstall("weather-tool")
    """
```

##### list_installed
```python
async def list_installed(
    self,
    outdated_only: bool = False
) -> List[InstalledPlugin]:
    """List installed plugins.
    
    Args:
        outdated_only: Only show outdated plugins
        
    Returns:
        List of installed plugins
        
    Example:
        plugins = await registry.list_installed()
        for p in plugins:
            print(f"{p.name} v{p.version}")
    """
```

##### publish
```python
async def publish(
    self,
    manifest_path: Union[str, Path],
    dry_run: bool = False
) -> PublishResult:
    """Publish a plugin to registry.
    
    Args:
        manifest_path: Path to plugin.yaml
        dry_run: Validate without publishing
        
    Returns:
        Publish result
        
    Example:
        result = await registry.publish("./plugin.yaml")
    """
```

### Version

```python
class Version:
    """Semantic version implementation.
    
    Attributes:
        major (int): Major version
        minor (int): Minor version  
        patch (int): Patch version
        prerelease (List[Union[str, int]]): Pre-release identifiers
        build (List[str]): Build metadata
        
    Example:
        v = Version("1.2.3-beta.1+build.123")
        print(v.major)  # 1
        print(v.is_prerelease)  # True
    """
    
    def __init__(self, version_string: str):
        """Parse version string.
        
        Args:
            version_string: Semantic version string
            
        Raises:
            ValueError: If version format is invalid
        """
```

#### Methods

##### bump_major/minor/patch
```python
def bump_major(self) -> "Version":
    """Increment major version."""
    
def bump_minor(self) -> "Version":
    """Increment minor version."""
    
def bump_patch(self) -> "Version":
    """Increment patch version."""
```

##### bump_prerelease
```python
def bump_prerelease(self) -> "Version":
    """Increment pre-release version.
    
    Example:
        v = Version("1.0.0-alpha")
        v2 = v.bump_prerelease()  # 1.0.0-alpha.1
    """
```

##### is_compatible_with
```python
def is_compatible_with(self, version_spec: str) -> bool:
    """Check compatibility with version spec.
    
    Args:
        version_spec: Version specification
        
    Returns:
        True if compatible
        
    Example:
        v = Version("1.2.3")
        v.is_compatible_with("^1.0.0")  # True
    """
```

##### satisfies
```python
def satisfies(self, constraint: str) -> bool:
    """Check if version satisfies constraint.
    
    Args:
        constraint: Version constraint
        
    Returns:
        True if satisfies
        
    Example:
        v = Version("1.5.0")
        v.satisfies(">=1.0.0,<2.0.0")  # True
    """
```

### VersionRange

```python
class VersionRange:
    """Version range specification.
    
    Supports multiple range formats:
    - Caret ranges: ^1.2.3
    - Tilde ranges: ~1.2.3
    - Comparisons: >=1.0.0, <2.0.0
    - Exact: =1.2.3
    - Wildcards: 1.2.*, 1.*
    
    Example:
        range = VersionRange("^1.0.0")
        range.allows(Version("1.5.0"))  # True
    """
    
    def __init__(self, spec: str):
        """Parse version range specification.
        
        Args:
            spec: Version range string
        """
```

#### Methods

##### allows
```python
def allows(self, version: Version) -> bool:
    """Check if version is allowed by range.
    
    Args:
        version: Version to check
        
    Returns:
        True if allowed
        
    Example:
        range = VersionRange(">=1.0.0,<2.0.0")
        range.allows(Version("1.5.0"))  # True
    """
```

##### intersect
```python
def intersect(self, other: "VersionRange") -> "VersionRange":
    """Get intersection of two ranges.
    
    Args:
        other: Another version range
        
    Returns:
        Intersection range
        
    Example:
        r1 = VersionRange(">=1.0.0")
        r2 = VersionRange("<2.0.0")
        r3 = r1.intersect(r2)  # >=1.0.0,<2.0.0
    """
```

### DependencyResolver

```python
class DependencyResolver:
    """Resolve plugin dependencies.
    
    Uses a SAT solver approach to find compatible versions
    that satisfy all constraints.
    
    Example:
        resolver = DependencyResolver()
        resolver.add_dependency("my-plugin", "dep1", "^1.0.0")
        solution = resolver.resolve()
    """
    
    def __init__(self, registry_client: Optional[RegistryClient] = None):
        """Initialize resolver.
        
        Args:
            registry_client: Registry client for version lookup
        """
```

#### Methods

##### add_dependency
```python
def add_dependency(
    self,
    package: str,
    dependency: str,
    version_spec: str
) -> None:
    """Add a dependency requirement.
    
    Args:
        package: Package requiring the dependency
        dependency: Dependency name
        version_spec: Version specification
        
    Example:
        resolver.add_dependency(
            "my-plugin",
            "agenticraft",
            ">=0.2.0"
        )
    """
```

##### resolve
```python
async def resolve(self) -> Dict[str, Version]:
    """Resolve all dependencies.
    
    Returns:
        Dictionary of package -> version
        
    Raises:
        VersionConflict: If conflicts exist
        
    Example:
        solution = await resolver.resolve()
        for pkg, ver in solution.items():
            print(f"{pkg}: {ver}")
    """
```

## Data Models

### PluginInfo

```python
class PluginInfo(BaseModel):
    """Plugin information from registry.
    
    Attributes:
        name (str): Plugin name
        description (str): Description
        latest_version (Version): Latest version
        versions (List[Version]): All versions
        author (str): Author name
        downloads (int): Download count
        rating (float): Average rating
        tags (List[str]): Tags
        created_at (datetime): Creation date
        updated_at (datetime): Last update
    """
    
    name: str
    description: str
    latest_version: Version
    versions: List[Version]
    author: str
    downloads: int = 0
    rating: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
```

### InstalledPlugin

```python
class InstalledPlugin(BaseModel):
    """Installed plugin information.
    
    Attributes:
        name (str): Plugin name
        version (Version): Installed version
        manifest (PluginManifest): Plugin manifest
        location (Path): Installation path
        dependencies (Dict[str, Version]): Resolved dependencies
        installed_at (datetime): Installation time
    """
    
    name: str
    version: Version
    manifest: PluginManifest
    location: Path
    dependencies: Dict[str, Version] = Field(default_factory=dict)
    installed_at: datetime
    
    def is_outdated(self, latest: Version) -> bool:
        """Check if plugin is outdated."""
        return self.version < latest
```

### PublishResult

```python
class PublishResult(BaseModel):
    """Plugin publish result.
    
    Attributes:
        success (bool): Whether publish succeeded
        plugin_name (str): Published plugin name
        version (Version): Published version
        url (str): Plugin URL
        message (str, optional): Status message
        errors (List[str]): Any errors
    """
    
    success: bool
    plugin_name: str
    version: Version
    url: Optional[str] = None
    message: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
```

## Exceptions

### MarketplaceError

```python
class MarketplaceError(Exception):
    """Base exception for marketplace operations."""
    pass
```

### VersionError

```python
class VersionError(MarketplaceError):
    """Version-related errors."""
    pass
```

### VersionConflict

```python
class VersionConflict(VersionError):
    """Version conflict in dependencies.
    
    Attributes:
        package (str): Conflicting package
        requirements (List[Tuple[str, str]]): Conflicting requirements
    """
    
    def __init__(self, package: str, requirements: List[Tuple[str, str]]):
        self.package = package
        self.requirements = requirements
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format conflict message."""
```

### PluginNotFound

```python
class PluginNotFound(MarketplaceError):
    """Plugin not found in registry."""
    
    def __init__(self, name: str, version: Optional[str] = None):
        self.name = name
        self.version = version
        msg = f"Plugin '{name}'" + (f" version {version}" if version else "")
        super().__init__(f"{msg} not found")
```

### InstallError

```python
class InstallError(MarketplaceError):
    """Plugin installation error."""
    pass
```

## Utility Functions

### load_plugin

```python
async def load_plugin(
    name: str,
    config: Optional[Dict[str, Any]] = None,
    registry: Optional[RegistryClient] = None
) -> BaseTool:
    """Load an installed plugin.
    
    Args:
        name: Plugin name
        config: Plugin configuration
        registry: Registry client
        
    Returns:
        Initialized tool instance
        
    Example:
        tool = await load_plugin(
            "weather-tool",
            config={"api_key": "xxx"}
        )
    """
```

### validate_manifest

```python
def validate_manifest(
    manifest_path: Union[str, Path]
) -> Tuple[bool, List[str]]:
    """Validate a plugin manifest.
    
    Args:
        manifest_path: Path to plugin.yaml
        
    Returns:
        Tuple of (is_valid, errors)
        
    Example:
        valid, errors = validate_manifest("plugin.yaml")
        if not valid:
            print("Errors:", errors)
    """
```

### create_plugin_structure

```python
def create_plugin_structure(
    name: str,
    path: Path,
    template: str = "basic"
) -> None:
    """Create plugin directory structure.
    
    Args:
        name: Plugin name
        path: Target directory
        template: Template type
        
    Example:
        create_plugin_structure(
            "my-plugin",
            Path("./my-plugin"),
            template="tool"
        )
    """
```

## Constants and Enums

### PluginCategory

```python
class PluginCategory(str, Enum):
    """Plugin categories."""
    DATA_PROCESSING = "data-processing"
    API_INTEGRATION = "api-integration"
    UTILITIES = "utilities"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    COMMUNICATION = "communication"
    MONITORING = "monitoring"
    TESTING = "testing"
    OTHER = "other"
```

### PluginStatus

```python
class PluginStatus(str, Enum):
    """Plugin status in registry."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
```

### UpdatePolicy

```python
class UpdatePolicy(str, Enum):
    """Plugin update policies."""
    CONSERVATIVE = "conservative"  # Patch only
    BALANCED = "balanced"          # Minor updates
    AGGRESSIVE = "aggressive"      # Any updates
    MANUAL = "manual"             # No auto-updates
```

## Type Aliases

```python
# Common type aliases
PluginName = str
VersionSpec = str
PluginConfig = Dict[str, Any]
DependencyMap = Dict[PluginName, VersionSpec]
VersionSolution = Dict[PluginName, Version]
```

## Configuration

### RegistryConfig

```python
class RegistryConfig(BaseModel):
    """Registry client configuration.
    
    Attributes:
        registry_url (str): Registry base URL
        cache_dir (Path): Local cache directory
        timeout (int): Request timeout
        max_retries (int): Maximum retry attempts
        verify_ssl (bool): Verify SSL certificates
        proxy (str, optional): Proxy URL
    """
    
    registry_url: str = "https://registry.agenticraft.com"
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".agenticraft" / "cache")
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = True
    proxy: Optional[str] = None
```

## Next Steps

- [Marketplace Guide](README.md) - Overview and usage
- [Plugin Development](plugin-development.md) - Create plugins
- [Version Management](version-management.md) - Version strategies
- [Examples](../../examples/marketplace/) - Working examples
