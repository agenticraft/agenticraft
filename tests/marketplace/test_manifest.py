"""Tests for marketplace manifest schemas."""

from datetime import datetime

import pytest

from agenticraft.marketplace.manifest import (
    AGENT_MANIFEST_TEMPLATE,
    TOOL_MANIFEST_TEMPLATE,
    PluginAuthor,
    PluginCategory,
    PluginConfig,
    PluginDependency,
    PluginEndpoint,
    PluginLicense,
    PluginManifest,
    PluginType,
    create_manifest,
)


def test_plugin_author():
    """Test PluginAuthor model."""
    author = PluginAuthor(
        name="John Doe",
        email="john@example.com",
        url="https://johndoe.com",
        github="johndoe",
    )

    assert author.name == "John Doe"
    assert author.email == "john@example.com"
    assert str(author.url) == "https://johndoe.com/"
    assert author.github == "johndoe"


def test_plugin_dependency():
    """Test PluginDependency validation."""
    # Valid dependencies
    deps = [
        PluginDependency(name="requests", version="*"),
        PluginDependency(name="numpy", version="1.2.3"),
        PluginDependency(name="pandas", version=">=2.0.0"),
        PluginDependency(name="scipy", version="~1.9.0"),
        PluginDependency(name="matplotlib", version="^3.5.0"),
        PluginDependency(name="optional-lib", version="1.*", optional=True),
    ]

    for dep in deps:
        assert dep.name
        assert dep.version

    # Invalid version
    with pytest.raises(ValueError):
        PluginDependency(name="bad", version="invalid-version")


def test_plugin_config():
    """Test PluginConfig model."""
    config = PluginConfig(
        name="api_key",
        description="API key for the service",
        default_value=None,
        type="string",
        required=True,
        env_var="MY_API_KEY",
    )

    assert config.name == "api_key"
    assert config.required is True
    assert config.env_var == "MY_API_KEY"


def test_plugin_endpoint():
    """Test PluginEndpoint model."""
    endpoint = PluginEndpoint(
        path="/analyze",
        method="POST",
        description="Analyze text",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        output_schema={
            "type": "object",
            "properties": {
                "sentiment": {"type": "string"},
                "score": {"type": "number"},
            },
        },
    )

    assert endpoint.path == "/analyze"
    assert endpoint.method == "POST"
    assert "text" in endpoint.input_schema["properties"]


def test_plugin_manifest_basic():
    """Test basic PluginManifest creation."""
    manifest = PluginManifest(
        name="test-plugin",
        version="1.0.0",
        type=PluginType.TOOL,
        category=PluginCategory.UTILITY,
        title="Test Plugin",
        description="A test plugin",
        author={"name": "Test Author"},
        entry_point="test_plugin.main:TestPlugin",
    )

    assert manifest.name == "test-plugin"
    assert manifest.version == "1.0.0"
    assert manifest.type == PluginType.TOOL
    assert manifest.license == PluginLicense.MIT  # Default


def test_plugin_manifest_validation():
    """Test PluginManifest validation."""
    # Invalid name (uppercase)
    with pytest.raises(ValueError):
        PluginManifest(
            name="Test-Plugin",  # Should be lowercase
            version="1.0.0",
            type=PluginType.TOOL,
            title="Test",
            description="Test",
            author={"name": "Test"},
            entry_point="test.main:Test",
        )

    # Invalid name (spaces)
    with pytest.raises(ValueError):
        PluginManifest(
            name="test plugin",  # No spaces allowed
            version="1.0.0",
            type=PluginType.TOOL,
            title="Test",
            description="Test",
            author={"name": "Test"},
            entry_point="test.main:Test",
        )

    # Invalid version
    with pytest.raises(ValueError):
        PluginManifest(
            name="test-plugin",
            version="1.0",  # Should be semantic version
            type=PluginType.TOOL,
            title="Test",
            description="Test",
            author={"name": "Test"},
            entry_point="test.main:Test",
        )


def test_plugin_manifest_complete():
    """Test complete PluginManifest with all fields."""
    manifest = PluginManifest(
        name="advanced-tool",
        version="2.1.0-beta.1",
        type=PluginType.TOOL,
        category=PluginCategory.DEVELOPMENT,
        title="Advanced Tool",
        description="An advanced development tool",
        long_description="This is a much longer description...",
        author={"name": "Jane Doe", "email": "jane@example.com", "github": "janedoe"},
        license=PluginLicense.APACHE_2_0,
        homepage="https://example.com",
        repository="https://github.com/janedoe/advanced-tool",
        documentation="https://docs.example.com",
        entry_point="advanced_tool.main:AdvancedTool",
        requirements={
            "python": ">=3.10",
            "agenticraft": ">=0.2.0",
            "dependencies": [
                {"name": "requests", "version": ">=2.28.0"},
                {"name": "pydantic", "version": "^2.0.0"},
            ],
        },
        config=[
            {
                "name": "timeout",
                "description": "Request timeout",
                "type": "integer",
                "default_value": 30,
                "required": False,
            }
        ],
        tags=["development", "testing", "automation"],
        capabilities=["code_analysis", "test_generation"],
        endpoints=[
            {"path": "/analyze", "method": "POST", "description": "Analyze code"}
        ],
        examples=[
            {
                "name": "Basic usage",
                "code": "tool = AdvancedTool()\nresult = tool.analyze(code)",
            }
        ],
        published_at=datetime.now(),
        downloads=1000,
        rating=4.8,
        verified=True,
    )

    assert manifest.name == "advanced-tool"
    assert manifest.version == "2.1.0-beta.1"
    assert manifest.author.name == "Jane Doe"
    assert manifest.license == PluginLicense.APACHE_2_0
    assert len(manifest.tags) == 3
    assert manifest.downloads == 1000
    assert manifest.verified is True


def test_manifest_to_registry_format():
    """Test converting manifest to registry format."""
    manifest = PluginManifest(
        name="test-tool",
        version="1.0.0",
        type=PluginType.TOOL,
        title="Test Tool",
        description="A test tool",
        author={"name": "John Doe"},
        entry_point="test_tool:Tool",
        tags=["test", "example"],
    )

    registry_format = manifest.to_registry_format()

    assert registry_format["full_name"] == "John Doe/test-tool"
    assert "test-tool" in registry_format["search_text"]
    assert "test tool" in registry_format["search_text"]
    assert "test" in registry_format["search_text"]
    assert "john doe" in registry_format["search_text"]


def test_manifest_yaml_serialization():
    """Test YAML serialization and deserialization."""
    manifest = PluginManifest(
        name="yaml-test",
        version="1.0.0",
        type=PluginType.AGENT,
        title="YAML Test",
        description="Testing YAML",
        author={"name": "Tester"},
        entry_point="yaml_test:Agent",
    )

    # Convert to YAML
    yaml_content = manifest.to_yaml()
    assert "name: yaml-test" in yaml_content
    assert "version: 1.0.0" in yaml_content
    assert "type: agent" in yaml_content

    # Parse from YAML
    parsed = PluginManifest.from_yaml(yaml_content)
    assert parsed.name == manifest.name
    assert parsed.version == manifest.version
    assert parsed.type == manifest.type


def test_create_manifest_helper():
    """Test the create_manifest helper function."""
    manifest = create_manifest(
        plugin_type=PluginType.TOOL,
        name="helper-test",
        title="Helper Test Tool",
        author_name="Helper Tester",
        description="Custom description",
        tags=["helper", "test"],
        version="2.0.0",
    )

    assert manifest.name == "helper-test"
    assert manifest.title == "Helper Test Tool"
    assert manifest.author.name == "Helper Tester"
    assert manifest.description == "Custom description"
    assert manifest.version == "2.0.0"  # Overridden default
    assert manifest.entry_point == "helper_test.main:Plugin"


def test_manifest_templates():
    """Test that manifest templates are valid YAML."""
    # Test tool template
    tool_manifest = PluginManifest.from_yaml(TOOL_MANIFEST_TEMPLATE)
    assert tool_manifest.name == "my-awesome-tool"
    assert tool_manifest.type == PluginType.TOOL
    assert tool_manifest.category == PluginCategory.PRODUCTIVITY

    # Test agent template
    agent_manifest = PluginManifest.from_yaml(AGENT_MANIFEST_TEMPLATE)
    assert agent_manifest.name == "research-assistant"
    assert agent_manifest.type == PluginType.AGENT
    assert agent_manifest.category == PluginCategory.RESEARCH


def test_plugin_types_and_categories():
    """Test all plugin types and categories are valid."""
    # Test all types
    for plugin_type in PluginType:
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            type=plugin_type,
            title="Test",
            description="Test",
            author={"name": "Test"},
            entry_point="test:Plugin",
        )
        assert manifest.type == plugin_type

    # Test all categories
    for category in PluginCategory:
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            type=PluginType.TOOL,
            category=category,
            title="Test",
            description="Test",
            author={"name": "Test"},
            entry_point="test:Plugin",
        )
        assert manifest.category == category


def test_plugin_licenses():
    """Test all license types."""
    for license_type in PluginLicense:
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            type=PluginType.TOOL,
            license=license_type,
            title="Test",
            description="Test",
            author={"name": "Test"},
            entry_point="test:Plugin",
        )
        assert manifest.license == license_type
