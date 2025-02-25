"""
Tests for the text formatter tool.
"""

import pytest
from autogen_toolsmith.tools.catalog.utility_tools.text_formatter import TextFormatterTool


def test_initialization():
    """Test tool initialization."""
    tool = TextFormatterTool()
    assert tool.metadata.name == "text_formatter"
    assert tool.metadata.description == "Formats text in various ways such as uppercase, lowercase, title case, etc."
    assert tool.metadata.version == "0.1.0"
    assert tool.metadata.tags == ["text", "formatting", "utility"]
    assert tool.metadata.category == "utility_tools"


def test_to_upper():
    """Test uppercase conversion."""
    tool = TextFormatterTool()
    result = tool.run("hello world", to_upper=True)
    assert result == "HELLO WORLD"


def test_to_lower():
    """Test lowercase conversion."""
    tool = TextFormatterTool()
    result = tool.run("HELLO WORLD", to_lower=True)
    assert result == "hello world"


def test_to_title():
    """Test title case conversion."""
    tool = TextFormatterTool()
    result = tool.run("hello world", to_title=True)
    assert result == "Hello World"


def test_reverse():
    """Test text reversal."""
    tool = TextFormatterTool()
    result = tool.run("hello", reverse=True)
    assert result == "olleh"


def test_combined_transformations():
    """Test combined transformations."""
    tool = TextFormatterTool()
    result = tool.run("hello world", to_upper=True, reverse=True)
    assert result == "DLROW OLLEH"


def test_conflicting_options():
    """Test error handling for conflicting options."""
    tool = TextFormatterTool()
    with pytest.raises(ValueError):
        tool.run("hello world", to_upper=True, to_lower=True) 