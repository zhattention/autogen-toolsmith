"""
Tests for the TextProcessorTool.
"""

import pytest
from autogen_toolsmith.tools.base.tool_base import BaseTool
from autogen_toolsmith.tools.catalog.utility_tools.text_processor import TextProcessorTool


def test_initialization():
    """Test tool initialization."""
    tool = TextProcessorTool()
    assert tool.metadata.name == "text_processor"
    assert isinstance(tool, BaseTool)
    assert tool.metadata.category == "utility_tools"
    assert "text" in tool.metadata.tags
    assert "nlp" in tool.metadata.tags


def test_word_count():
    """Test the word_count operation."""
    tool = TextProcessorTool()
    
    # Basic test
    result = tool.run("This is a test", operation="word_count")
    assert result["word_count"] == 4
    assert result["char_count"] == 14
    assert result["char_count_no_spaces"] == 11
    assert result["sentence_count"] == 0
    assert result["paragraph_count"] == 1
    
    # Test with punctuation
    result = tool.run("This is a test. Another sentence!", operation="word_count")
    assert result["word_count"] == 7
    assert result["sentence_count"] == 2
    assert result["paragraph_count"] == 1
    
    # Test with multiple paragraphs
    result = tool.run("Paragraph one.\n\nParagraph two.", operation="word_count")
    assert result["word_count"] == 5
    assert result["sentence_count"] == 2
    assert result["paragraph_count"] == 2


def test_case_conversion():
    """Test the case conversion operations."""
    tool = TextProcessorTool()
    
    # Upper case
    result = tool.run("This is a test", operation="case_upper")
    assert result["converted"] == "THIS IS A TEST"
    assert result["case_type"] == "upper"
    
    # Lower case
    result = tool.run("This is a test", operation="case_lower")
    assert result["converted"] == "this is a test"
    assert result["case_type"] == "lower"
    
    # Title case
    result = tool.run("this is a test", operation="case_title")
    assert result["converted"] == "This Is A Test"
    assert result["case_type"] == "title"
    
    # Capitalize
    result = tool.run("this is a test", operation="case_capitalize")
    assert result["converted"] == "This is a test"
    assert result["case_type"] == "capitalize"
    
    # Swap case
    result = tool.run("This is a TEST", operation="case_swap")
    assert result["converted"] == "tHIS IS A test"
    assert result["case_type"] == "swap"


def test_extract_words():
    """Test the extract_words operation."""
    tool = TextProcessorTool()
    
    result = tool.run("This is a test with some duplicate words. This is a test.", operation="extract_words")
    assert "words" in result
    assert len(result["words"]) > 0
    assert "unique_words" in result
    assert len(result["unique_words"]) < len(result["words"])
    assert result["word_count"] == len(result["words"])
    assert result["unique_word_count"] == len(result["unique_words"])
    assert "This" in result["words"]
    assert "is" in result["words"]
    assert "test" in result["words"]


def test_summarize():
    """Test the summarize operation."""
    tool = TextProcessorTool()
    
    # Test with short text (should return the original)
    short_text = "Short text."
    result = tool.run(short_text, operation="summarize")
    assert result["summary"] == short_text
    assert result["reduction"] == 0
    
    # Test with longer text
    long_text = "This is the first sentence. This is the second sentence. This is the third sentence. This is the last sentence."
    result = tool.run(long_text, operation="summarize")
    assert "This is the first sentence" in result["summary"]
    assert "This is the last sentence" in result["summary"]
    assert result["reduction"] > 0
    assert result["original_length"] == len(long_text)
    assert result["summary_length"] < result["original_length"]


def test_empty_input():
    """Test handling of empty input."""
    tool = TextProcessorTool()
    
    result = tool.run("", operation="word_count")
    assert "error" in result
    assert result["error"] == "Empty text provided"


def test_invalid_operation():
    """Test handling of invalid operations."""
    tool = TextProcessorTool()
    
    with pytest.raises(ValueError) as excinfo:
        tool.run("This is a test", operation="invalid_operation")
    
    assert "Unknown operation" in str(excinfo.value)


def test_signature():
    """Test the tool signature generation."""
    tool = TextProcessorTool()
    signature = tool.get_signature()
    
    assert signature["name"] == "text_processor"
    assert "parameters" in signature
    assert "text" in signature["parameters"]
    assert "operation" in signature["parameters"] 