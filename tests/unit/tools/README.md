# Tool Testing Documentation

## Overview

This document describes the testing approach for AgentiCraft's built-in tools.

## Test Structure

```
tests/tools/
├── __init__.py
├── test_calculator_tools.py  # Tests for mathematical operations
├── test_file_tools.py        # Tests for file operations
└── test_web_tools.py         # Tests for web operations
```

## Testing Strategy

### 1. Calculator Tools (`test_calculator_tools.py`)

**Coverage Areas:**
- Basic arithmetic operations
- Order of operations
- Floating-point calculations
- Mathematical functions (sqrt, sin, cos, log, etc.)
- Constants (pi, e)
- Complex expressions
- Error handling for invalid expressions
- Security (no eval/exec/import allowed)
- Tool metadata validation

**Key Test Cases:**
- `TestCalculateTool`: Tests the basic calculator
- `TestScientificCalculateTool`: Tests advanced calculations with explanations
- `TestSafeFunctions`: Ensures security boundaries

### 2. File Operation Tools (`test_file_tools.py`)

**Coverage Areas:**
- Reading text files with various encodings
- Writing files with overwrite protection
- Directory listing with patterns
- JSON file operations
- File metadata retrieval
- Path handling (relative, absolute, ~expansion)
- Error conditions (missing files, permissions)

**Key Test Cases:**
- `TestReadFileTool`: File reading scenarios
- `TestWriteFileTool`: File writing with safety checks
- `TestListFilesTool`: Directory operations
- `TestJsonTools`: JSON-specific operations
- `TestFileInfoTool`: Metadata extraction

**Fixtures:**
- `temp_dir`: Creates isolated test directory
- `sample_files`: Pre-populated test file structure

### 3. Web Tools (`test_web_tools.py`)

**Coverage Areas:**
- Web search with different types (general, news, academic)
- Text extraction from URLs
- Metadata retrieval
- URL validation and checking
- Mock implementations (no real HTTP calls)

**Key Test Cases:**
- `TestWebSearchTool`: Search functionality
- `TestExtractTextTool`: Content extraction
- `TestGetPageMetadataTool`: Metadata parsing
- `TestCheckUrlTool`: URL validation

**Note:** These are mock implementations. Real implementations would require:
- HTTP client (aiohttp)
- HTML parser (BeautifulSoup4)
- API keys for search services
- Rate limiting and caching

## Running Tests

### Run all tool tests:
```bash
pytest tests/tools/ -v
```

### Run specific test file:
```bash
pytest tests/tools/test_calculator_tools.py -v
```

### Run specific test class:
```bash
pytest tests/tools/test_calculator_tools.py::TestCalculateTool -v
```

### Run specific test method:
```bash
pytest tests/tools/test_calculator_tools.py::TestCalculateTool::test_basic_arithmetic -v
```

### Run with coverage:
```bash
pytest tests/tools/ --cov=agenticraft.tools --cov-report=html
```

## Test Patterns

### 1. Async Testing
All async tools use `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_async_tool(self):
    result = await some_tool("input")
    assert result == expected
```

### 2. Error Testing
Use `pytest.raises` for expected errors:
```python
with pytest.raises(ValueError, match="Expected error message"):
    tool_function(bad_input)
```

### 3. Parametrized Tests
For testing multiple inputs:
```python
@pytest.mark.parametrize("input,expected", [
    ("2+2", 4),
    ("3*3", 9),
])
def test_calculations(self, input, expected):
    assert calculate(input) == expected
```

### 4. Fixture Usage
Temporary directories for file operations:
```python
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
```

## Mock vs Real Implementation

Current web tools are mocked. For production:

1. **Replace mock responses** with actual HTTP calls
2. **Add retry logic** for network failures  
3. **Implement caching** to reduce API calls
4. **Add rate limiting** to respect API limits
5. **Handle authentication** for API keys

## Security Considerations

### Calculator Tools
- No access to `eval`, `exec`, `__import__`
- Limited to safe mathematical operations
- No file system or network access

### File Tools  
- Path validation prevents directory traversal
- File size limits prevent memory exhaustion
- Overwrite protection by default

### Web Tools
- URL validation before requests
- Content size limits
- No JavaScript execution
- Sanitized outputs

## Future Improvements

1. **Integration Tests**: Test tools working together
2. **Performance Tests**: Benchmark tool execution
3. **Stress Tests**: Large files, many concurrent operations
4. **Real API Tests**: Optional tests against real services
5. **Property-Based Tests**: Use hypothesis for edge cases

## Debugging Failed Tests

1. **Check test output**: Run with `-vv` for verbose output
2. **Examine fixtures**: Ensure test data is created correctly
3. **Isolate the test**: Run single test to avoid interference
4. **Check async behavior**: Ensure proper await usage
5. **Verify mocks**: Confirm mock data matches expected format
