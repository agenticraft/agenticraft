"""Minimal test file to verify pytest works."""

def test_simple():
    """Simple test that should always pass."""
    assert 1 + 1 == 2

def test_import_pytest():
    """Test that pytest is available."""
    import pytest
    assert pytest is not None

class TestBasic:
    """Basic test class."""
    
    def test_in_class(self):
        """Test in a class."""
        assert True
