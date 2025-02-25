"""
Tests for the text analyzer tool.
"""

import pytest
from unittest.mock import patch, MagicMock
from autogen_toolsmith.tools.catalog.utility_tools.text_analyzer import TextAnalyzerTool


def test_initialization():
    """Test tool initialization."""
    tool = TextAnalyzerTool()
    assert tool.metadata.name == "text_analyzer"
    assert tool.metadata.description == "Analyzes text to provide metrics such as character count, word count, and average word length"
    assert tool.metadata.version == "0.1.0"
    assert tool.metadata.dependencies == ["text_formatter"]
    assert tool.metadata.tags == ["text", "analysis", "utility"]
    assert tool.metadata.category == "utility_tools"


@patch('autogen_toolsmith.tools.get_tool')
def test_basic_analysis(mock_get_tool):
    """Test basic text analysis without normalization."""
    # Setup mock
    mock_formatter = MagicMock()
    mock_get_tool.return_value = mock_formatter
    
    # Run test
    tool = TextAnalyzerTool()
    result = tool.run("Hello World")
    
    # Assertions
    mock_get_tool.assert_called_once_with("text_formatter")
    # Formatter shouldn't be used when normalize=False
    mock_formatter.run.assert_not_called()
    
    assert result["char_count"] == 10
    assert result["word_count"] == 2
    assert result["avg_word_length"] == 5.0


@patch('autogen_toolsmith.tools.get_tool')
def test_normalized_analysis(mock_get_tool):
    """Test text analysis with normalization."""
    # Setup mock
    mock_formatter = MagicMock()
    mock_formatter.run.return_value = "hello world"
    mock_get_tool.return_value = mock_formatter
    
    # Run test
    tool = TextAnalyzerTool()
    result = tool.run("Hello World", normalize=True)
    
    # Assertions
    mock_get_tool.assert_called_once_with("text_formatter")
    mock_formatter.run.assert_called_once_with("Hello World", to_lower=True)
    
    assert result["char_count"] == 10
    assert result["word_count"] == 2
    assert result["avg_word_length"] == 5.0


@patch('autogen_toolsmith.tools.get_tool')
def test_detailed_analysis(mock_get_tool):
    """Test detailed text analysis."""
    # Setup mock
    mock_formatter = MagicMock()
    mock_get_tool.return_value = mock_formatter
    
    # Run test
    tool = TextAnalyzerTool()
    result = tool.run("Hello World. This is a test.", detailed=True)
    
    # Assertions
    assert result["char_count"] == 24
    assert result["word_count"] == 6
    assert result["avg_word_length"] == 4.0
    assert result["unique_word_count"] == 6  # All words are unique
    assert result["lexical_diversity"] == 1.0
    assert result["sentence_count"] == 2
    assert result["avg_words_per_sentence"] == 3.0


@patch('autogen_toolsmith.tools.get_tool')
def test_missing_dependency(mock_get_tool):
    """Test error handling when the dependency is missing."""
    # Setup mock to return None (dependency not found)
    mock_get_tool.return_value = None
    
    # Run test
    tool = TextAnalyzerTool()
    with pytest.raises(ValueError, match="Required dependency 'text_formatter' not found"):
        tool.run("Hello World") 