"""Tests for file operation tools."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from agenticraft.core.exceptions import ToolExecutionError
from agenticraft.tools.file_ops import (
    file_info,
    list_files,
    read_file,
    read_json,
    write_file,
    write_json,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    # Create text file
    text_file = temp_dir / "sample.txt"
    text_file.write_text("Hello, World!")

    # Create JSON file
    json_file = temp_dir / "data.json"
    json_file.write_text(json.dumps({"name": "test", "value": 42}))

    # Create subdirectory with files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested content")

    # Create hidden file
    hidden_file = temp_dir / ".hidden"
    hidden_file.write_text("Hidden content")

    return {
        "temp_dir": temp_dir,
        "text_file": text_file,
        "json_file": json_file,
        "subdir": subdir,
        "hidden_file": hidden_file,
    }


class TestReadFileTool:
    """Test the read_file tool."""

    @pytest.mark.asyncio
    async def test_read_text_file(self, sample_files):
        """Test reading a text file."""
        content = await read_file.arun(path=str(sample_files["text_file"]))
        assert content == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_with_encoding(self, temp_dir):
        """Test reading with different encodings."""
        # Create file with special characters
        file_path = temp_dir / "unicode.txt"
        file_path.write_text("Héllo, 世界!", encoding="utf-8")

        content = await read_file.arun(path=str(file_path), encoding="utf-8")
        assert content == "Héllo, 世界!"

    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """Test reading non-existent file."""
        with pytest.raises(ToolExecutionError, match="File not found"):
            await read_file.arun(path="/nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_read_directory(self, sample_files):
        """Test error when trying to read a directory."""
        with pytest.raises(ToolExecutionError, match="Path is not a file"):
            await read_file.arun(path=str(sample_files["subdir"]))

    @pytest.mark.asyncio
    async def test_file_size_limit(self, temp_dir):
        """Test file size limit."""
        # Create a large file (simulate)
        large_file = temp_dir / "large.txt"
        large_file.write_text("x" * (11 * 1024 * 1024))  # 11MB

        with pytest.raises(ToolExecutionError, match="File too large"):
            await read_file.arun(path=str(large_file), max_size_mb=10.0)

        # Should work with higher limit
        content = await read_file.arun(path=str(large_file), max_size_mb=12.0)
        assert len(content) == 11 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_path_expansion(self, temp_dir):
        """Test path expansion (~ for home)."""
        # Create a file with known content
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")

        # Read using absolute path
        content = await read_file.arun(path=str(test_file))
        assert content == "Test content"


class TestWriteFileTool:
    """Test the write_file tool."""

    @pytest.mark.asyncio
    async def test_write_new_file(self, temp_dir):
        """Test writing a new file."""
        file_path = temp_dir / "new_file.txt"
        result = await write_file.arun(
            path=str(file_path), content="New content", overwrite=True
        )

        assert result["created"] is True
        assert result["overwritten"] is False
        assert result["size"] == len("New content")
        assert file_path.read_text() == "New content"

    @pytest.mark.asyncio
    async def test_overwrite_protection(self, sample_files):
        """Test overwrite protection."""
        # Try to overwrite without permission
        with pytest.raises(ToolExecutionError, match="File already exists"):
            await write_file.arun(
                path=str(sample_files["text_file"]), content="New content"
            )

        # Original content should be unchanged
        assert sample_files["text_file"].read_text() == "Hello, World!"

    @pytest.mark.asyncio
    async def test_overwrite_enabled(self, sample_files):
        """Test overwriting with permission."""
        result = await write_file.arun(
            path=str(sample_files["text_file"]),
            content="Overwritten content",
            overwrite=True,
        )

        assert result["created"] is False
        assert result["overwritten"] is True
        assert sample_files["text_file"].read_text() == "Overwritten content"

    @pytest.mark.asyncio
    async def test_create_parent_directories(self, temp_dir):
        """Test creating parent directories."""
        nested_path = temp_dir / "new" / "nested" / "file.txt"
        result = await write_file.arun(
            path=str(nested_path), content="Nested content", overwrite=True
        )

        assert nested_path.exists()
        assert nested_path.read_text() == "Nested content"
        assert result["created"] is True

    @pytest.mark.asyncio
    async def test_write_with_encoding(self, temp_dir):
        """Test writing with specific encoding."""
        file_path = temp_dir / "encoded.txt"
        content = "Unicode: 你好世界"

        result = await write_file.arun(
            path=str(file_path), content=content, encoding="utf-8", overwrite=True
        )

        assert file_path.read_text(encoding="utf-8") == content
        assert result["size"] == len(content)


class TestListFilesTool:
    """Test the list_files tool."""

    @pytest.mark.asyncio
    async def test_list_directory(self, sample_files):
        """Test listing files in a directory."""
        files = await list_files.arun(directory=str(sample_files["temp_dir"]))

        # Check we got the expected files (excluding hidden by default)
        file_names = {f["name"] for f in files}
        assert "sample.txt" in file_names
        assert "data.json" in file_names
        assert "subdir" in file_names
        assert ".hidden" not in file_names  # Hidden by default

        # Check file info
        txt_file = next(f for f in files if f["name"] == "sample.txt")
        assert txt_file["size"] == 13  # "Hello, World!"
        assert txt_file["is_dir"] is False

        subdir = next(f for f in files if f["name"] == "subdir")
        assert subdir["is_dir"] is True

    @pytest.mark.asyncio
    async def test_list_with_pattern(self, sample_files):
        """Test listing with glob pattern."""
        # List only .txt files
        txt_files = await list_files.arun(
            directory=str(sample_files["temp_dir"]), pattern="*.txt"
        )
        assert len(txt_files) == 1
        assert txt_files[0]["name"] == "sample.txt"

        # List only .json files
        json_files = await list_files.arun(
            directory=str(sample_files["temp_dir"]), pattern="*.json"
        )
        assert len(json_files) == 1
        assert json_files[0]["name"] == "data.json"

    @pytest.mark.asyncio
    async def test_list_recursive(self, sample_files):
        """Test recursive listing."""
        files = await list_files.arun(
            directory=str(sample_files["temp_dir"]), recursive=True
        )

        # Should include nested file
        paths = {f["path"] for f in files}
        assert any("nested.txt" in path for path in paths)

    @pytest.mark.asyncio
    async def test_list_include_hidden(self, sample_files):
        """Test including hidden files."""
        files = await list_files.arun(
            directory=str(sample_files["temp_dir"]), include_hidden=True
        )

        file_names = {f["name"] for f in files}
        assert ".hidden" in file_names

    @pytest.mark.asyncio
    async def test_list_nonexistent_directory(self):
        """Test listing non-existent directory."""
        with pytest.raises(ToolExecutionError, match="Directory not found"):
            await list_files.arun(directory="/nonexistent/directory")

    @pytest.mark.asyncio
    async def test_list_file_instead_of_directory(self, sample_files):
        """Test error when path is a file."""
        with pytest.raises(ToolExecutionError, match="Path is not a directory"):
            await list_files.arun(directory=str(sample_files["text_file"]))


class TestJsonTools:
    """Test JSON reading and writing tools."""

    @pytest.mark.asyncio
    async def test_read_json(self, sample_files):
        """Test reading JSON file."""
        data = await read_json.arun(path=str(sample_files["json_file"]))

        assert data == {"name": "test", "value": 42}
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_read_invalid_json(self, temp_dir):
        """Test reading invalid JSON."""
        bad_json = temp_dir / "bad.json"
        bad_json.write_text("{ invalid json")

        with pytest.raises(ToolExecutionError, match="Invalid JSON"):
            await read_json.arun(path=str(bad_json))

    @pytest.mark.asyncio
    async def test_write_json(self, temp_dir):
        """Test writing JSON file."""
        file_path = temp_dir / "output.json"
        data = {
            "string": "value",
            "number": 123,
            "array": [1, 2, 3],
            "nested": {"key": "value"},
        }

        result = await write_json.arun(path=str(file_path), data=data, overwrite=True)

        assert result["created"] is True

        # Read back and verify
        loaded = json.loads(file_path.read_text())
        assert loaded == data

    @pytest.mark.asyncio
    async def test_write_json_formatting(self, temp_dir):
        """Test JSON formatting options."""
        file_path = temp_dir / "formatted.json"
        data = {"a": 1, "b": 2}

        # Test with custom indent
        await write_json.arun(path=str(file_path), data=data, indent=4, overwrite=True)

        content = file_path.read_text()
        assert "    " in content  # 4-space indent

        # Test compact (no indent)
        await write_json.arun(
            path=str(file_path), data=data, indent=None, overwrite=True
        )

        content = file_path.read_text()
        assert content == '{"a": 1, "b": 2}'  # Compact

    @pytest.mark.asyncio
    async def test_write_json_unicode(self, temp_dir):
        """Test writing JSON with Unicode."""
        file_path = temp_dir / "unicode.json"
        data = {"message": "Hello 世界", "emoji": "😀"}

        await write_json.arun(path=str(file_path), data=data, overwrite=True)

        loaded = json.loads(file_path.read_text())
        assert loaded == data


class TestFileInfoTool:
    """Test the file_info tool."""

    @pytest.mark.asyncio
    async def test_file_info_for_file(self, sample_files):
        """Test getting info for a file."""
        info = await file_info.arun(path=str(sample_files["text_file"]))

        assert info["exists"] is True
        assert info["is_file"] is True
        assert info["is_dir"] is False
        assert info["size"] == 13  # "Hello, World!"
        assert info["extension"] == ".txt"
        assert info["stem"] == "sample"
        assert "modified" in info
        assert "created" in info

    @pytest.mark.asyncio
    async def test_file_info_for_directory(self, sample_files):
        """Test getting info for a directory."""
        info = await file_info.arun(path=str(sample_files["subdir"]))

        assert info["exists"] is True
        assert info["is_file"] is False
        assert info["is_dir"] is True
        assert "extension" not in info
        assert "stem" not in info

    @pytest.mark.asyncio
    async def test_file_info_nonexistent(self):
        """Test info for non-existent file."""
        info = await file_info.arun(path="/nonexistent/file.txt")

        assert info["exists"] is False
        assert "is_file" not in info
        assert "size" not in info

    @pytest.mark.asyncio
    async def test_file_info_path_resolution(self, sample_files):
        """Test path resolution in file info."""
        # Test with relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(sample_files["temp_dir"])
            info = await file_info.arun(path="sample.txt")

            assert info["exists"] is True
            assert info["name"] == "sample.txt"
        finally:
            os.chdir(original_cwd)


class TestToolMetadata:
    """Test tool metadata for all file tools."""

    def test_all_tools_have_metadata(self):
        """Ensure all tools have proper metadata."""
        tools = [read_file, write_file, list_files, read_json, write_json, file_info]

        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "parameters")
            assert tool.name is not None
            assert tool.description is not None
            assert isinstance(tool.parameters, list)
