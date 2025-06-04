#!/usr/bin/env python3
"""Run spell check and link validation on documentation."""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set
from urllib.parse import urlparse


def get_markdown_files() -> List[Path]:
    """Get all markdown files in the project."""
    files = []
    
    # Check docs directory
    docs_dir = Path("docs")
    if docs_dir.exists():
        files.extend(docs_dir.rglob("*.md"))
    
    # Check root README
    if Path("README.md").exists():
        files.append(Path("README.md"))
    
    # Check other markdown files
    for md_file in Path(".").glob("*.md"):
        if md_file not in files:
            files.append(md_file)
    
    return files


def extract_links(content: str) -> Set[str]:
    """Extract all links from markdown content."""
    links = set()
    
    # Markdown links: [text](url)
    md_links = re.findall(r'\[.*?\]\((.*?)\)', content)
    links.update(md_links)
    
    # Direct URLs
    url_pattern = r'https?://[^\s\)"\'<>]+'
    direct_urls = re.findall(url_pattern, content)
    links.update(direct_urls)
    
    return links


def validate_link(link: str, base_path: Path) -> tuple[bool, str]:
    """Validate a single link."""
    # Parse the link
    parsed = urlparse(link)
    
    # External link
    if parsed.scheme in ['http', 'https']:
        # For CI, we'll just check format, not actual connectivity
        return True, "External link (not checked in CI)"
    
    # Internal link
    if not parsed.scheme:
        # Remove anchor
        path = link.split('#')[0]
        if not path:  # Just an anchor
            return True, "Anchor link"
        
        # Check if file exists
        full_path = base_path.parent / path
        if full_path.exists():
            return True, "File exists"
        else:
            return False, f"File not found: {full_path}"
    
    return True, "Unknown link type"


def check_spelling(file_path: Path) -> List[str]:
    """Check spelling in a file using aspell or hunspell."""
    errors = []
    
    # Try aspell first
    try:
        result = subprocess.run(
            ['aspell', 'list', '-l', 'en', '-p', './agenticraft.dict'],
            input=file_path.read_text(),
            capture_output=True,
            text=True
        )
        
        misspelled = result.stdout.strip().split('\n')
        misspelled = [word for word in misspelled if word]
        
        # Filter out technical terms
        technical_terms = {
            'agenticraft', 'mcp', 'llm', 'api', 'json', 'yaml', 'async',
            'asyncio', 'pytest', 'mypy', 'ruff', 'mkdocs', 'pydantic',
            'openai', 'anthropic', 'telemetry', 'observability', 'config',
            'env', 'cli', 'args', 'kwargs', 'docstring', 'isinstance'
        }
        
        misspelled = [word for word in misspelled 
                     if word.lower() not in technical_terms]
        
        if misspelled:
            errors.extend(misspelled)
            
    except FileNotFoundError:
        print("⚠️  aspell not found, skipping spell check")
        print("   Install with: brew install aspell (macOS) or apt-get install aspell (Linux)")
    
    return errors


def main():
    """Run documentation quality checks."""
    print("📝 Documentation Quality Check")
    print("=" * 60)
    
    all_good = True
    
    # Get all markdown files
    md_files = get_markdown_files()
    print(f"\nFound {len(md_files)} markdown files to check")
    
    # Check each file
    for md_file in md_files:
        print(f"\n📄 Checking {md_file}")
        
        with open(md_file, 'r') as f:
            content = f.read()
        
        # Extract and validate links
        links = extract_links(content)
        if links:
            print(f"   Found {len(links)} links")
            
            broken_links = []
            for link in links:
                valid, message = validate_link(link, md_file)
                if not valid:
                    broken_links.append((link, message))
            
            if broken_links:
                all_good = False
                print("   ❌ Broken links found:")
                for link, error in broken_links:
                    print(f"      - {link}: {error}")
            else:
                print("   ✅ All links valid")
        
        # Check spelling
        spelling_errors = check_spelling(md_file)
        if spelling_errors:
            # Unique errors only
            unique_errors = list(set(spelling_errors))
            if unique_errors:
                all_good = False
                print(f"   ❌ Spelling errors: {', '.join(unique_errors[:10])}")
                if len(unique_errors) > 10:
                    print(f"      ... and {len(unique_errors) - 10} more")
        else:
            print("   ✅ Spelling check passed")
    
    # Check Python docstrings
    print("\n\n📚 Checking Python Docstrings")
    print("-" * 60)
    
    py_files = list(Path("agenticraft").rglob("*.py"))
    docstring_issues = 0
    
    for py_file in py_files:
        with open(py_file, 'r') as f:
            content = f.read()
        
        # Basic docstring checks
        if 'def ' in content or 'class ' in content:
            # Count functions/classes without docstrings
            missing = 0
            
            # Simple heuristic - look for def/class not followed by docstring
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith(('def ', 'class ')):
                    # Check next non-empty line for docstring
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    
                    if j < len(lines):
                        next_line = lines[j].strip()
                        if not (next_line.startswith('"""') or next_line.startswith("'''")):
                            missing += 1
            
            if missing > 0:
                docstring_issues += missing
                print(f"⚠️  {py_file}: {missing} functions/classes missing docstrings")
    
    if docstring_issues == 0:
        print("✅ All functions and classes have docstrings")
    else:
        all_good = False
        print(f"\n❌ Total missing docstrings: {docstring_issues}")
    
    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print("✅ All documentation quality checks passed!")
        return 0
    else:
        print("❌ Documentation quality issues found")
        print("\nSuggestions:")
        print("- Fix broken links or update paths")
        print("- Add missing docstrings")
        print("- Review spelling errors (some may be technical terms)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
