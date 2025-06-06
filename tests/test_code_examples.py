#!/usr/bin/env python3
"""Standalone script to validate all code examples in documentation and docstrings.

This is NOT a pytest test file - it's a standalone validation script.
Run directly with: python tests/test_code_examples.py
"""

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple


def extract_code_blocks_from_markdown(content: str) -> List[Tuple[str, int]]:
    """Extract Python code blocks from markdown content."""
    pattern = r'```python\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    code_blocks = []
    for match in matches:
        # Get line number for better error reporting
        line_num = content[:content.find(match)].count('\n') + 1
        code_blocks.append((match, line_num))
    
    return code_blocks


def extract_docstring_examples(file_path: Path) -> List[Tuple[str, str, int]]:
    """Extract example code from docstrings."""
    examples = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return examples
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)
            if docstring and 'Example:' in docstring:
                # Extract code after Example:
                example_start = docstring.find('Example:')
                example_section = docstring[example_start:]
                
                # Look for code blocks
                code_match = re.search(r'```python\n(.*?)\n```', example_section, re.DOTALL)
                if not code_match:
                    # Try without language specifier
                    code_match = re.search(r'```\n(.*?)\n```', example_section, re.DOTALL)
                
                if code_match:
                    examples.append((
                        code_match.group(1),
                        f"{file_path}:{node.name}",
                        node.lineno
                    ))
    
    return examples


def validate_code_block(code: str, context: str) -> Tuple[bool, str]:
    """Validate a code block and return success status and error message."""
    # Add common imports that might be assumed
    test_code = """
import sys
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock any common objects that might be referenced
try:
    from agenticraft.core.agent import Agent
    from agenticraft.core.tool import Tool
    from agenticraft.core.workflow import Workflow
    from agenticraft.providers.openai import OpenAIProvider
except ImportError:
    pass

# Test code starts here
""" + code
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        # Try to run the code
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, result.stderr
        
        # Also check for syntax by compiling
        compile(code, context, 'exec')
        
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Code execution timed out"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


def main():
    """Test all code examples."""
    print("🧪 Testing Code Examples in Documentation")
    print("=" * 60)
    
    errors = []
    total_examples = 0
    passed_examples = 0
    
    # Test examples in markdown docs
    docs_dir = Path("docs")
    if docs_dir.exists():
        for md_file in docs_dir.rglob("*.md"):
            print(f"\n📄 Checking {md_file}")
            
            with open(md_file, 'r') as f:
                content = f.read()
            
            code_blocks = extract_code_blocks_from_markdown(content)
            
            for code, line_num in code_blocks:
                total_examples += 1
                context = f"{md_file}:line {line_num}"
                
                # Skip certain patterns that aren't meant to be run
                if any(skip in code for skip in ['...', '# TODO', '# Your code here']):
                    print(f"  ⏭️  Skipping placeholder example at line {line_num}")
                    continue
                
                success, error = validate_code_block(code, context)
                
                if success:
                    passed_examples += 1
                    print(f"  ✅ Example at line {line_num}")
                else:
                    errors.append((context, error))
                    print(f"  ❌ Example at line {line_num}")
                    print(f"     Error: {error.split('Error:')[-1].strip()}")
    
    # Test examples in docstrings
    print("\n\n📚 Checking Docstring Examples")
    print("-" * 60)
    
    for py_file in Path("agenticraft").rglob("*.py"):
        examples = extract_docstring_examples(py_file)
        
        if examples:
            print(f"\n📄 {py_file}")
            
            for code, location, line_num in examples:
                total_examples += 1
                
                # Skip placeholders
                if any(skip in code for skip in ['...', '# TODO', '# Your code here']):
                    print(f"  ⏭️  Skipping placeholder in {location}")
                    continue
                
                success, error = validate_code_block(code, location)
                
                if success:
                    passed_examples += 1
                    print(f"  ✅ {location}")
                else:
                    errors.append((location, error))
                    print(f"  ❌ {location}")
                    print(f"     Error: {error.split('Error:')[-1].strip()}")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total examples found: {total_examples}")
    print(f"Examples passed: {passed_examples}")
    print(f"Examples failed: {len(errors)}")
    
    if errors:
        print("\n❌ Failed examples:")
        for location, error in errors[:10]:  # Show first 10
            print(f"\n  {location}")
            print(f"  {error[:200]}...")  # First 200 chars of error
        
        if len(errors) > 10:
            print(f"\n  ... and {len(errors) - 10} more errors")
        
        return 1
    else:
        print("\n✅ All code examples passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
