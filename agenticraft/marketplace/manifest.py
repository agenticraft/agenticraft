"""Plugin manifest schema for AgentiCraft marketplace.

This module defines the schema for plugin manifests, which describe
tools, agents, and other extensions available in the marketplace.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class PluginType(str, Enum):
    """Types of plugins available in the marketplace."""

    TOOL = "tool"
    AGENT = "agent"
    MEMORY = "memory"
    PROVIDER = "provider"
    WORKFLOW = "workflow"
    REASONING = "reasoning"


class PluginCategory(str, Enum):
    """Categories for organizing plugins."""

    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    DATA = "data"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    CREATIVE = "creative"
    UTILITY = "utility"
    INTEGRATION = "integration"
    OTHER = "other"


class PluginLicense(str, Enum):
    """Common open source licenses."""

    MIT = "MIT"
    APACHE_2_0 = "Apache-2.0"
    GPL_3_0 = "GPL-3.0"
    BSD_3_CLAUSE = "BSD-3-Clause"
    UNLICENSE = "Unlicense"
    PROPRIETARY = "Proprietary"
    OTHER = "Other"


class PluginAuthor(BaseModel):
    """Plugin author information."""

    name: str
    email: str | None = None
    url: HttpUrl | None = None
    github: str | None = None


class PluginDependency(BaseModel):
    """Plugin dependency specification."""

    name: str
    version: str = "*"
    optional: bool = False

    @field_validator("version")
    def validate_version(cls, v: str) -> str:
        """Validate version specification."""
        # Support common version patterns
        valid_patterns = [
            r"^\*$",  # Any version
            r"^\d+\.\d+\.\d+$",  # Exact version
            r"^[><=~^]+\d+\.\d+\.\d+$",  # Version range
            r"^\d+\.\d+\.\*$",  # Minor version wildcard
            r"^\d+\.\*$",  # Major version wildcard
        ]

        import re

        if not any(re.match(pattern, v) for pattern in valid_patterns):
            raise ValueError(f"Invalid version specification: {v}")

        return v


class PluginRequirements(BaseModel):
    """Plugin system requirements."""

    python: str = ">=3.10"
    agenticraft: str = ">=0.2.0"
    dependencies: list[PluginDependency] = Field(default_factory=list)
    system: dict[str, str] | None = None  # OS-specific requirements


class PluginConfig(BaseModel):
    """Plugin configuration schema."""

    name: str
    description: str
    default_value: Any
    type: str
    required: bool = False
    env_var: str | None = None


class PluginEndpoint(BaseModel):
    """API endpoint exposed by the plugin."""

    path: str
    method: str = "POST"
    description: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class PluginManifest(BaseModel):
    """Complete plugin manifest schema.

    This defines the structure of plugin.yaml files that describe
    plugins in the AgentiCraft marketplace.
    """

    # Basic information
    name: str = Field(description="Unique plugin identifier (e.g., 'web-browser-tool')")
    version: str = Field(description="Semantic version (e.g., '1.0.0')")
    type: PluginType = Field(description="Type of plugin")
    category: PluginCategory = Field(
        default=PluginCategory.OTHER, description="Plugin category for organization"
    )

    # Description
    title: str = Field(description="Human-readable title")
    description: str = Field(description="Short description (one line)")
    long_description: str | None = Field(
        default=None, description="Detailed description (markdown)"
    )

    # Metadata
    author: PluginAuthor
    license: PluginLicense = PluginLicense.MIT
    homepage: HttpUrl | None = None
    repository: HttpUrl | None = None
    documentation: HttpUrl | None = None

    # Technical details
    entry_point: str = Field(
        description="Module path to main entry point (e.g., 'my_plugin.main:MyTool')"
    )
    requirements: PluginRequirements = Field(default_factory=PluginRequirements)

    # Configuration
    config: list[PluginConfig] = Field(
        default_factory=list, description="Configuration options"
    )

    # Features
    tags: list[str] = Field(
        default_factory=list, description="Tags for search and discovery"
    )
    capabilities: list[str] = Field(
        default_factory=list, description="List of capabilities provided"
    )

    # API endpoints (for tools/services)
    endpoints: list[PluginEndpoint] = Field(
        default_factory=list, description="API endpoints exposed"
    )

    # Examples
    examples: list[dict[str, Any]] = Field(
        default_factory=list, description="Usage examples"
    )

    # Registry metadata
    published_at: datetime | None = None
    updated_at: datetime | None = None
    downloads: int = 0
    rating: float | None = None
    verified: bool = False

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        """Validate plugin name format."""
        import re

        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Plugin name must contain only lowercase letters, "
                "numbers, and hyphens"
            )
        return v

    @field_validator("version")
    def validate_version(cls, v: str) -> str:
        """Validate semantic version."""
        import re

        if not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", v):
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        return v

    def to_registry_format(self) -> dict[str, Any]:
        """Convert to format for registry storage."""
        data = self.dict()

        # Add computed fields
        data["full_name"] = f"{self.author.name}/{self.name}"
        data["search_text"] = " ".join(
            [
                self.name,
                self.title,
                self.description,
                " ".join(self.tags),
                self.author.name,
            ]
        ).lower()

        return data

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "PluginManifest":
        """Create manifest from YAML content.

        Args:
            yaml_content: YAML string

        Returns:
            PluginManifest instance
        """
        import yaml

        data = yaml.safe_load(yaml_content)
        return cls(**data)

    def to_yaml(self) -> str:
        """Convert manifest to YAML format.

        Returns:
            YAML string
        """
        import yaml

        data = self.dict(exclude_none=True)

        # Convert enums to their string values
        if "type" in data and hasattr(data["type"], "value"):
            data["type"] = data["type"].value
        if "category" in data and hasattr(data["category"], "value"):
            data["category"] = data["category"].value
        if "license" in data and hasattr(data["license"], "value"):
            data["license"] = data["license"].value

        # Handle author
        if "author" in data and isinstance(data["author"], dict):
            # Already a dict, good
            pass
        elif "author" in data and hasattr(data["author"], "dict"):
            data["author"] = data["author"].dict(exclude_none=True)

        # Handle requirements
        if "requirements" in data and hasattr(data["requirements"], "dict"):
            data["requirements"] = data["requirements"].dict(exclude_none=True)

        # Handle config items
        if "config" in data:
            config_list = []
            for cfg in data["config"]:
                if hasattr(cfg, "dict"):
                    config_list.append(cfg.dict(exclude_none=True))
                else:
                    config_list.append(cfg)
            data["config"] = config_list

        return yaml.dump(data, default_flow_style=False, sort_keys=False)


# Example manifest templates

TOOL_MANIFEST_TEMPLATE = """
name: my-awesome-tool
version: 1.0.0
type: tool
category: productivity

title: My Awesome Tool
description: A tool that does awesome things
long_description: |
  This tool provides amazing functionality for AgentiCraft agents.
  
  Features:
  - Feature 1
  - Feature 2
  - Feature 3

author:
  name: Your Name
  email: your.email@example.com
  github: yourusername

license: MIT
homepage: https://example.com/my-tool
repository: https://github.com/yourusername/my-awesome-tool
documentation: https://docs.example.com/my-tool

entry_point: my_awesome_tool.main:AwesomeTool

requirements:
  python: ">=3.10"
  agenticraft: ">=0.2.0"
  dependencies:
    - name: requests
      version: ">=2.28.0"
    - name: beautifulsoup4
      version: ">=4.11.0"
      optional: true

config:
  - name: api_key
    description: API key for the service
    type: string
    default_value: null
    required: true
    env_var: MY_TOOL_API_KEY
  - name: timeout
    description: Request timeout in seconds
    type: integer
    default_value: 30
    required: false

tags:
  - web
  - api
  - automation

capabilities:
  - web_scraping
  - api_integration
  - data_extraction

endpoints:
  - path: /scrape
    method: POST
    description: Scrape a web page
    input_schema:
      type: object
      properties:
        url:
          type: string
          description: URL to scrape
      required: [url]
    output_schema:
      type: object
      properties:
        content:
          type: string
        title:
          type: string

examples:
  - name: Basic web scraping
    code: |
      from agenticraft import Agent
      from my_awesome_tool import AwesomeTool
      
      agent = Agent()
      agent.add_tool(AwesomeTool())
      
      result = agent.run("Scrape https://example.com")
      print(result.content)
""".strip()


AGENT_MANIFEST_TEMPLATE = """
name: research-assistant
version: 1.0.0
type: agent
category: research

title: Research Assistant Agent
description: An intelligent research assistant for comprehensive information gathering

author:
  name: AgentiCraft Team
  email: team@agenticraft.ai

license: Apache-2.0

entry_point: research_assistant.agent:ResearchAssistant

requirements:
  agenticraft: ">=0.2.0"
  dependencies:
    - name: web-browser-tool
      version: ">=1.0.0"
    - name: document-analyzer
      version: ">=1.0.0"

config:
  - name: max_sources
    description: Maximum number of sources to research
    type: integer
    default_value: 10

tags:
  - research
  - analysis
  - information-gathering

capabilities:
  - web_research
  - source_verification
  - summary_generation
  - citation_management
""".strip()


def create_manifest(
    plugin_type: PluginType, name: str, title: str, author_name: str, **kwargs
) -> PluginManifest:
    """Helper function to create a plugin manifest.

    Args:
        plugin_type: Type of plugin
        name: Plugin identifier
        title: Human-readable title
        author_name: Author name
        **kwargs: Additional manifest fields

    Returns:
        PluginManifest instance
    """
    defaults = {
        "version": "1.0.0",
        "description": f"A {plugin_type} plugin for AgentiCraft",
        "author": {"name": author_name},
        "entry_point": f"{name.replace('-', '_')}.main:Plugin",
    }

    # Merge with provided kwargs
    defaults.update(kwargs)

    return PluginManifest(name=name, type=plugin_type, title=title, **defaults)
