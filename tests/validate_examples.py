#!/usr/bin/env python3
"""Validate that all examples follow the required structure."""

import ast
import sys
from pathlib import Path


def validate_example(file_path: Path) -> list[str]:
    """Validate a single example file."""
    errors = []

    with open(file_path) as f:
        content = f.read()

    # Check shebang
    lines = content.split("\n")
    if not lines[0].startswith("#!/usr/bin/env python3"):
        errors.append(f"{file_path.name}: Missing or incorrect shebang")

    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        errors.append(f"{file_path.name}: Syntax error - {e}")
        return errors

    # Check for docstring
    has_docstring = False
    if tree.body and isinstance(tree.body[0], ast.Expr):
        if isinstance(tree.body[0].value, ast.Str):
            has_docstring = True

    if not has_docstring:
        errors.append(f"{file_path.name}: Missing module docstring")

    # Check for main function
    has_main = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            if node.name == "main":
                has_main = True
                # Check if main has docstring
                if not (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Str)
                ):
                    errors.append(
                        f"{file_path.name}: main() function missing docstring"
                    )

    if not has_main:
        errors.append(f"{file_path.name}: Missing main() function")

    # Check for if __name__ == "__main__"
    has_main_guard = False
    for node in tree.body:
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and isinstance(node.test.comparators[0], ast.Str)
            and node.test.comparators[0].s == "__main__"
        ):
            has_main_guard = True

    if not has_main_guard:
        errors.append(f"{file_path.name}: Missing if __name__ == '__main__' guard")

    return errors


def main():
    """Validate all examples."""
    print("🔍 Validating AgentiCraft Examples")
    print("=" * 60)

    examples_dir = Path("examples")
    errors = []

    # Check main examples
    for py_file in examples_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        file_errors = validate_example(py_file)
        if file_errors:
            errors.extend(file_errors)
        else:
            print(f"✅ {py_file.name}")

    # Check MCP examples
    mcp_dir = examples_dir / "mcp"
    if mcp_dir.exists():
        for py_file in mcp_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            file_errors = validate_example(py_file)
            if file_errors:
                errors.extend(file_errors)
            else:
                print(f"✅ mcp/{py_file.name}")

    # Check plugin examples
    plugins_dir = examples_dir / "plugins"
    if plugins_dir.exists():
        for py_file in plugins_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            # Plugin files may not need main()
            file_errors = []
            with open(py_file) as f:
                content = f.read()

            # Still check for docstring
            try:
                tree = ast.parse(content)
                if not (
                    tree.body
                    and isinstance(tree.body[0], ast.Expr)
                    and isinstance(tree.body[0].value, ast.Str)
                ):
                    file_errors.append(
                        f"plugins/{py_file.name}: Missing module docstring"
                    )
            except SyntaxError as e:
                file_errors.append(f"plugins/{py_file.name}: Syntax error - {e}")

            if file_errors:
                errors.extend(file_errors)
            else:
                print(f"✅ plugins/{py_file.name}")

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print("❌ Validation failed with errors:\n")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("✅ All examples validated successfully!")
        return 0


if __name__ == "__main__":

    sys.exit(main())