"""Test that examples run without errors."""

import importlib.util
from pathlib import Path

import pytest

# Get the examples directory
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


class TestExamples:
    """Test example files can be imported and run."""

    def get_example_files(self, subdirectory: str = None):
        """Get all Python example files."""
        if subdirectory:
            example_path = EXAMPLES_DIR / subdirectory
        else:
            example_path = EXAMPLES_DIR

        if not example_path.exists():
            return []

        # Get all .py files except __init__.py
        return [
            f
            for f in example_path.rglob("*.py")
            if f.name != "__init__.py" and not f.name.startswith("test_")
        ]

    @pytest.mark.parametrize(
        "category",
        [
            "providers",
            "agents",
            "memory",
            "reasoning",
            "streaming",
            "workflows",
        ],
    )
    def test_examples_importable(self, category):
        """Test that example files can be imported."""
        example_files = self.get_example_files(category)

        if not example_files:
            pytest.skip(f"No examples found in {category}")

        for example_file in example_files[:3]:  # Test first 3 examples per category
            # Create module name
            module_name = f"test_example_{example_file.stem}"

            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, example_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)

                # Try to load it
                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    # Skip if it requires API keys or external services
                    if "api_key" in str(e).lower() or "connection" in str(e).lower():
                        pytest.skip(f"Example requires external service: {e}")
                    else:
                        raise

    def test_provider_examples_structure(self):
        """Test that provider examples follow expected structure."""
        provider_examples = self.get_example_files("providers")

        for example_file in provider_examples:
            content = example_file.read_text()

            # Check for common patterns
            assert (
                "from agenticraft import Agent" in content
                or "import agenticraft" in content
            )
            assert "async def" in content or "def main" in content
            assert "__name__" in content  # Should have if __name__ == "__main__"

    @pytest.mark.skip("Streaming examples may require live API")
    def test_streaming_examples(self):
        """Test streaming examples."""
        streaming_examples = self.get_example_files("streaming")

        for example_file in streaming_examples[:1]:  # Just test one
            # These likely need API keys, so just check structure
            content = example_file.read_text()
            assert "stream" in content.lower()
            assert "async" in content
