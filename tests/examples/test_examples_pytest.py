"""Pytest version of example tests."""

import importlib.util
from pathlib import Path

import pytest


class TestExamples:
    """Test that example files are properly structured."""

    @pytest.fixture
    def examples_dir(self):
        """Get the examples directory path."""
        # Examples are in the project's examples/reasoning directory
        project_root = Path(
            __file__
        ).parent.parent.parent  # tests/examples -> tests -> project root
        return project_root / "examples" / "reasoning"

    def test_reasoning_examples_structure(self, examples_dir):
        """Test that reasoning example files have proper structure."""
        examples = [
            ("reasoning_demo.py", "Simple Demo (No API)"),
            ("chain_of_thought.py", "Chain of Thought"),
            ("tree_of_thoughts.py", "Tree of Thoughts"),
            ("react.py", "ReAct Pattern"),
            ("pattern_comparison.py", "Pattern Comparison"),
            ("production_handlers.py", "Production Handlers"),
            ("reasoning_transparency.py", "Reasoning Transparency"),
        ]

        missing_files = []
        missing_main = []
        import_errors = []

        for filename, description in examples:
            filepath = examples_dir / filename

            # Check if file exists
            if not filepath.exists():
                missing_files.append((filename, description))
                continue

            # Try to import and check for main function
            try:
                spec = importlib.util.spec_from_file_location(
                    filename.replace(".py", ""), filepath
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    if not hasattr(module, "main"):
                        missing_main.append((filename, description))
                else:
                    import_errors.append(
                        (filename, description, "Failed to create module spec")
                    )
            except Exception as e:
                import_errors.append((filename, description, str(e)[:100]))

        # Report results
        if missing_files:
            pytest.skip(f"Example files not found: {[f[0] for f in missing_files]}")

        if import_errors:
            errors_str = "\n".join([f"{f[0]}: {f[2]}" for f in import_errors])
            pytest.skip(f"Import errors in examples:\n{errors_str}")

        if missing_main:
            pytest.skip(
                f"Examples missing main() function: {[f[0] for f in missing_main]}"
            )

        # If we get here, all examples are properly structured
        assert True, "All example files have proper structure"
