"""File operations tools for agents.

Provides safe file reading, writing, and manipulation capabilities.
"""

import json
from pathlib import Path
from typing import Any

from ..core.tool import tool


async def _read_file(
    path: str, encoding: str = "utf-8", max_size_mb: float = 10.0
) -> str:
    """Read contents of a file.

    Args:
        path: Path to the file
        encoding: File encoding (default: utf-8)
        max_size_mb: Maximum file size in MB to read

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too large

    Example:
        >>> await read_file("data.txt")
        "Hello, World!"
    """
    file_path = Path(path).expanduser().resolve()

    # Security checks
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    # Check file size
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"File too large: {size_mb:.2f}MB (max: {max_size_mb}MB)")

    # Read file
    try:
        return file_path.read_text(encoding=encoding)
    except Exception as e:
        raise ValueError(f"Failed to read file: {e}")


@tool(
    name="read_file",
    description="Read contents of a text file. Supports various encodings.",
)
async def read_file(
    path: str, encoding: str = "utf-8", max_size_mb: float = 10.0
) -> str:
    """Read contents of a file.

    Args:
        path: Path to the file
        encoding: File encoding (default: utf-8)
        max_size_mb: Maximum file size in MB to read

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too large

    Example:
        >>> await read_file("data.txt")
        "Hello, World!"
    """
    return await _read_file(path, encoding, max_size_mb)


async def _write_file(
    path: str, content: str, encoding: str = "utf-8", overwrite: bool = False
) -> dict[str, Any]:
    """Write content to a file.

    Args:
        path: Path to write to
        content: Content to write
        encoding: File encoding
        overwrite: Whether to overwrite existing files

    Returns:
        Dictionary with operation details

    Example:
        >>> await write_file("output.txt", "Hello!", overwrite=True)
        {'path': 'output.txt', 'size': 6, 'created': True}
    """
    file_path = Path(path).expanduser().resolve()

    # Check if file exists
    exists = file_path.exists()
    if exists and not overwrite:
        raise ValueError(f"File already exists: {path}. Set overwrite=True to replace.")

    # Create parent directories
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    file_path.write_text(content, encoding=encoding)

    return {
        "path": str(file_path),
        "size": len(content),
        "created": not exists,
        "overwritten": exists and overwrite,
    }


@tool(
    name="write_file",
    description="Write content to a file. Creates directories if needed.",
)
async def write_file(
    path: str, content: str, encoding: str = "utf-8", overwrite: bool = False
) -> dict[str, Any]:
    """Write content to a file.

    Args:
        path: Path to write to
        content: Content to write
        encoding: File encoding
        overwrite: Whether to overwrite existing files

    Returns:
        Dictionary with operation details

    Example:
        >>> await write_file("output.txt", "Hello!", overwrite=True)
        {'path': 'output.txt', 'size': 6, 'created': True}
    """
    return await _write_file(path, content, encoding, overwrite)


@tool(
    name="list_files", description="List files in a directory with optional filtering."
)
async def list_files(
    directory: str = ".",
    pattern: str = "*",
    recursive: bool = False,
    include_hidden: bool = False,
) -> list[dict[str, Any]]:
    """List files in a directory.

    Args:
        directory: Directory to list
        pattern: Glob pattern for filtering
        recursive: Whether to search recursively
        include_hidden: Whether to include hidden files

    Returns:
        List of file information dictionaries

    Example:
        >>> await list_files(".", pattern="*.py")
        [{'name': 'main.py', 'size': 1024, 'is_dir': False}, ...]
    """
    dir_path = Path(directory).expanduser().resolve()

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    # Get files
    if recursive:
        paths = dir_path.rglob(pattern)
    else:
        paths = dir_path.glob(pattern)

    # Build file list
    files = []
    for path in paths:
        # Skip hidden files if requested
        if not include_hidden and path.name.startswith("."):
            continue

        try:
            stat = path.stat()
            files.append(
                {
                    "name": path.name,
                    "path": str(path.relative_to(dir_path)),
                    "size": stat.st_size,
                    "is_dir": path.is_dir(),
                    "modified": stat.st_mtime,
                }
            )
        except Exception:
            # Skip files we can't stat
            continue

    # Sort by name
    files.sort(key=lambda x: x["name"])

    return files


@tool(name="read_json", description="Read and parse a JSON file.")
async def read_json(path: str) -> Any:
    """Read and parse JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON data

    Example:
        >>> await read_json("config.json")
        {'setting': 'value'}
    """
    content = await _read_file(path)
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")


@tool(name="write_json", description="Write data to a JSON file with formatting.")
async def write_json(
    path: str, data: Any, indent: int = 2, overwrite: bool = False
) -> dict[str, Any]:
    """Write data to JSON file.

    Args:
        path: Path to write to
        data: Data to serialize as JSON
        indent: Indentation level
        overwrite: Whether to overwrite existing file

    Returns:
        Operation details

    Example:
        >>> await write_json("data.json", {"key": "value"})
        {'path': 'data.json', 'size': 18, 'created': True}
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    return await _write_file(path, content, overwrite=overwrite)


@tool(
    name="file_info", description="Get detailed information about a file or directory."
)
async def file_info(path: str) -> dict[str, Any]:
    """Get detailed file or directory information.

    Args:
        path: Path to inspect

    Returns:
        Dictionary with file/directory details

    Example:
        >>> await file_info("document.txt")
        {
            'path': 'document.txt',
            'exists': True,
            'is_file': True,
            'size': 1024,
            'extension': '.txt'
        }
    """
    file_path = Path(path).expanduser().resolve()

    info = {
        "path": str(file_path),
        "name": file_path.name,
        "exists": file_path.exists(),
    }

    if file_path.exists():
        stat = file_path.stat()
        info.update(
            {
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
            }
        )

        if file_path.is_file():
            info["extension"] = file_path.suffix
            info["stem"] = file_path.stem

    return info
