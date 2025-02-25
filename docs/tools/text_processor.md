# Text Processor Tool

The Text Processor Tool provides functionality for common text processing operations. It's designed to handle a variety of text transformations, extractions, and analysis tasks.

## Overview

The tool enables operations such as:
- Word and character counting
- Case conversion (upper, lower, title, capitalize, swap)
- Word extraction and analysis
- Basic text summarization

## Usage

```python
from autogen_toolsmith.tools import get_tool

# Get the tool
text_processor = get_tool("text_processor")

# Count statistics
stats = text_processor.run("This is a sample text.", operation="word_count")
print(stats)
# {'word_count': 5, 'char_count': 21, 'char_count_no_spaces': 18, 'sentence_count': 1, 'paragraph_count': 1}

# Convert case
upper_case = text_processor.run("This is a sample text.", operation="case_upper")
print(upper_case["converted"])
# "THIS IS A SAMPLE TEXT."

# Extract words
words = text_processor.run("This is a sample text.", operation="extract_words")
print(words["unique_words"])
# ['This', 'is', 'a', 'sample', 'text']

# Summarize text
long_text = """Machine learning is a subfield of artificial intelligence that focuses on developing systems that can learn from data. 
It has applications in many areas including computer vision, natural language processing, and recommendation systems. 
Recent advances in deep learning have dramatically improved the performance of machine learning systems."""

summary = text_processor.run(long_text, operation="summarize")
print(summary["summary"])
# Extractive summary of the text
```

## Available Operations

### word_count

Counts words, characters, sentences, and paragraphs in the text.

**Returns:**
- `word_count`: Number of words
- `char_count`: Total number of characters
- `char_count_no_spaces`: Number of characters excluding spaces
- `sentence_count`: Number of sentences
- `paragraph_count`: Number of paragraphs

### case_[type]

Converts the case of the text, where `[type]` can be:
- `upper`: Convert to uppercase
- `lower`: Convert to lowercase
- `title`: Convert to title case
- `capitalize`: Capitalize the first character
- `swap`: Swap the case of each character

**Returns:**
- `original`: The original text
- `converted`: The converted text
- `case_type`: The case type used for conversion

### extract_words

Extracts all words from the text.

**Returns:**
- `words`: List of all words
- `unique_words`: List of unique words
- `word_count`: Number of words
- `unique_word_count`: Number of unique words

### summarize

Generates a simple extractive summary of the text.

**Returns:**
- `summary`: The generated summary
- `original_length`: Length of the original text
- `summary_length`: Length of the summary
- `reduction`: Percentage of reduction in length

## Error Handling

The tool handles empty text gracefully and raises appropriate exceptions for invalid operations. 