"""Comprehensive tests for CLI new command."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agenticraft.cli.commands.new import (
    AVAILABLE_TEMPLATES,
    _copy_template,
    _get_template_path,
    _init_git,
    _update_project_files,
    new,
)


class TestNewCommand:
    """Test the new command for creating projects."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return tmp_path

    def test_new_basic_project(self, runner, temp_dir):
        """Test creating a basic project."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            result = runner.invoke(new, ["my-project"])

            assert result.exit_code == 0
            assert "Creating new basic project: my-project" in result.output
            assert "✨ Project 'my-project' created successfully!" in result.output

            # Check project directory was created
            project_path = Path("my-project")
            assert project_path.exists()
            assert project_path.is_dir()

    def test_new_with_template(self, runner, temp_dir):
        """Test creating a project with a specific template."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Mock template path to avoid actual template files
            mock_template_path = temp_dir / "templates" / "fastapi"
            mock_template_path.mkdir(parents=True)
            (mock_template_path / "main.py").write_text("# FastAPI template")

            with patch(
                "agenticraft.cli.commands.new._get_template_path",
                return_value=mock_template_path,
            ):
                result = runner.invoke(new, ["my-api", "--template", "fastapi"])

                assert result.exit_code == 0
                assert "Creating new fastapi project: my-api" in result.output
                assert (
                    "docker-compose up" in result.output
                )  # FastAPI specific instruction

    def test_new_with_custom_directory(self, runner, temp_dir):
        """Test creating a project in a custom directory."""
        with runner.isolated_filesystem(temp_dir=temp_dir) as isolated_dir:
            # Create custom directory inside the isolated filesystem
            custom_dir = Path("custom")
            custom_dir.mkdir()

            # Create a mock template directory inside the isolated filesystem
            mock_template_path = Path(isolated_dir) / "mock_templates" / "basic"
            mock_template_path.mkdir(parents=True)
            (mock_template_path / "main.py").write_text("# Basic template")

            with patch(
                "agenticraft.cli.commands.new._get_template_path",
                return_value=mock_template_path,
            ):
                result = runner.invoke(new, ["my-project", "--directory", "custom"])

                # Debug output if test fails
                if result.exit_code != 0:
                    print(f"Exit code: {result.exit_code}")
                    print(f"Output: {result.output}")
                    print(f"Exception: {result.exception}")

                assert result.exit_code == 0
                project_path = custom_dir / "my-project"
                assert project_path.exists()

    def test_new_directory_already_exists(self, runner, temp_dir):
        """Test error when project directory already exists."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Create existing directory
            existing = Path("existing-project")
            existing.mkdir()

            result = runner.invoke(new, ["existing-project"])

            assert result.exit_code != 0
            assert "Error: Directory" in result.output
            assert "already exists" in result.output

    def test_new_no_git_flag(self, runner, temp_dir):
        """Test creating a project without git initialization."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Mock template path
            mock_template_path = temp_dir / "templates" / "basic"
            mock_template_path.mkdir(parents=True)
            (mock_template_path / "main.py").write_text("# Basic template")

            with patch(
                "agenticraft.cli.commands.new._get_template_path",
                return_value=mock_template_path,
            ):
                with patch("agenticraft.cli.commands.new._init_git") as mock_init_git:
                    result = runner.invoke(new, ["my-project", "--no-git"])

                    assert result.exit_code == 0
                    # Git init should not be called
                    mock_init_git.assert_not_called()

    def test_new_template_not_found(self, runner, temp_dir):
        """Test error when template doesn't exist."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Mock template path that doesn't exist
            mock_template_path = temp_dir / "templates" / "nonexistent"

            with patch(
                "agenticraft.cli.commands.new._get_template_path",
                return_value=mock_template_path,
            ):
                result = runner.invoke(new, ["my-project", "--template", "basic"])

                assert result.exit_code != 0
                assert "Error: Template 'basic' not found" in result.output
                assert "Available templates:" in result.output

    def test_new_copy_error_cleanup(self, runner, temp_dir):
        """Test that project directory is cleaned up on error."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Mock template path
            mock_template_path = temp_dir / "templates" / "basic"
            mock_template_path.mkdir(parents=True)

            with patch(
                "agenticraft.cli.commands.new._get_template_path",
                return_value=mock_template_path,
            ):
                with patch(
                    "agenticraft.cli.commands.new._copy_template",
                    side_effect=Exception("Copy failed"),
                ):
                    result = runner.invoke(new, ["my-project"])

                    assert result.exit_code != 0
                    assert "Error creating project: Copy failed" in result.output
                    # Project directory should be cleaned up
                    assert not Path("my-project").exists()

    def test_available_templates(self):
        """Test that all expected templates are available."""
        assert "basic" in AVAILABLE_TEMPLATES
        assert "fastapi" in AVAILABLE_TEMPLATES
        assert "cli" in AVAILABLE_TEMPLATES
        assert "bot" in AVAILABLE_TEMPLATES
        assert "mcp-server" in AVAILABLE_TEMPLATES

    def test_new_cli_template_instructions(self, runner, temp_dir):
        """Test CLI template specific instructions."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Mock template path
            mock_template_path = temp_dir / "templates" / "cli"
            mock_template_path.mkdir(parents=True)
            (mock_template_path / "main.py").write_text("# CLI template")

            with patch(
                "agenticraft.cli.commands.new._get_template_path",
                return_value=mock_template_path,
            ):
                result = runner.invoke(new, ["my-cli", "--template", "cli"])

                assert result.exit_code == 0
                assert "python -m venv venv" in result.output
                assert "pip install -e ." in result.output
                assert "my-cli --help" in result.output


class TestNewCommandHelpers:
    """Test helper functions for the new command."""

    def test_get_template_path_dev_mode(self, tmp_path):
        """Test getting template path in development mode."""
        # This test is checking if we can find templates in development mode
        # Since the function uses __file__ to find the path, we'll test the logic
        # by checking that the function returns a valid path structure

        path = _get_template_path("basic")

        # The path should end with templates/basic
        assert path.name == "basic"
        assert path.parent.name == "templates"

        # In dev mode or installed mode, the function should return a Path object
        assert isinstance(path, Path)

    def test_get_template_path_installed(self):
        """Test getting template path for installed package."""
        with patch("pathlib.Path.exists", return_value=False):
            path = _get_template_path("basic")
            assert "templates" in str(path)
            assert "basic" in str(path)

    def test_copy_template(self, tmp_path):
        """Test copying template files."""
        # Create source template
        src = tmp_path / "template"
        src.mkdir()
        (src / "main.py").write_text("print('hello')")
        (src / "subdir").mkdir()
        (src / "subdir" / "file.txt").write_text("content")

        # Create destination
        dst = tmp_path / "project"
        dst.mkdir()

        _copy_template(src, dst, "test-project")

        # Check files were copied
        assert (dst / "main.py").exists()
        assert (dst / "main.py").read_text() == "print('hello')"
        assert (dst / "subdir" / "file.txt").exists()
        assert (dst / "subdir" / "file.txt").read_text() == "content"

    def test_copy_template_ignores_special_dirs(self, tmp_path):
        """Test that special directories are ignored during copy."""
        src = tmp_path / "template"
        src.mkdir()
        (src / ".git").mkdir()
        (src / "__pycache__").mkdir()
        (src / ".pytest_cache").mkdir()
        (src / "main.py").write_text("content")

        dst = tmp_path / "project"
        dst.mkdir()

        _copy_template(src, dst, "test-project")

        # Special directories should not be copied
        assert not (dst / ".git").exists()
        assert not (dst / "__pycache__").exists()
        assert not (dst / ".pytest_cache").exists()
        # Regular files should be copied
        assert (dst / "main.py").exists()

    def test_init_git(self, tmp_path):
        """Test git initialization."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            _init_git(project_path)

            # Check git commands were called
            calls = mock_run.call_args_list
            assert len(calls) == 3  # init, add, commit

            # Check .gitignore was created
            gitignore = project_path / ".gitignore"
            assert gitignore.exists()
            content = gitignore.read_text()
            assert "__pycache__/" in content
            assert ".env" in content
            assert "venv/" in content

    def test_init_git_failure(self, tmp_path, capsys):
        """Test git initialization failure handling."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            _init_git(project_path)

            captured = capsys.readouterr()
            assert "Failed to initialize git repository" in captured.out

    def test_update_project_files(self, tmp_path):
        """Test updating project files with project name."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        # Create sample files
        pyproject = project_path / "pyproject.toml"
        pyproject.write_text(
            'name = "agenticraft-template"\n[project]\nname = "agenticraft-template"'
        )

        readme = project_path / "README.md"
        readme.write_text("# AgentiCraft Template\nThis is agenticraft-template")

        # Create docker-compose for fastapi template
        docker_dir = project_path / "docker"
        docker_dir.mkdir()
        compose = docker_dir / "docker-compose.yml"
        compose.write_text("services:\n  agenticraft-api:\n    name: agenticraft-api")

        _update_project_files(project_path, "my-awesome-project", "fastapi")

        # Check files were updated
        assert 'name = "my-awesome-project"' in pyproject.read_text()
        assert "my-awesome-project" in pyproject.read_text()

        assert "My-Awesome-Project" in readme.read_text()
        assert "my-awesome-project" in readme.read_text()

        assert "my-awesome-project" in compose.read_text()

    def test_update_project_files_missing_files(self, tmp_path):
        """Test update handles missing files gracefully."""
        project_path = tmp_path / "project"
        project_path.mkdir()

        # Should not raise error even if files don't exist
        _update_project_files(project_path, "test-project", "basic")
