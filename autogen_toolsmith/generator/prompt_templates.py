"""
Prompt templates for code generation.
"""

TOOL_TEMPLATE = """
You are an expert in developing Python tools for the AutoGen framework. Your task is to create a new tool based on the following specification:

# Tool Specification
{tool_specification}

# Available Dependencies
The tool can use the following dependencies:
{available_dependencies}

# Code Format Requirements
- Create a Python class that inherits from BaseTool
- The class should have a descriptive name ending with "Tool"
- Implement a `run` method with appropriate parameters based on the specification
- Include proper typing and documentation
- Handle errors gracefully
- Include example usage in docstrings
- Make sure all arguments to the constructor and run method are validated

# Tool Class Structure
The tool should follow this structure:

```python
from typing import Any, Dict, List, Optional
from autogen_toolsmith.tools.base.tool_base import BaseTool

class YourToolName(BaseTool):
    \"\"\"
    A detailed description of what your tool does.
    
    Example:
        >>> tool = YourToolName()
        >>> result = tool.run(...)
        >>> print(result)
    \"\"\"
    
    def __init__(self, ...):
        \"\"\"
        Initialize the tool.
        
        Args:
            param1: Description of parameter 1
            param2: Description of parameter 2
        \"\"\"
        super().__init__(
            name="your_tool_name",
            description="A brief description of your tool",
            version="0.1.0",
            author="AutoGen Toolsmith",
            dependencies=[],  # List any tool dependencies here
            tags=["tag1", "tag2"],
            category="utility_tools"  # Or "data_tools" or "api_tools"
        )
        # Initialize your tool's attributes
        
    def run(self, ...):
        \"\"\"
        Execute the tool's functionality.
        
        Args:
            param1: Description of parameter 1
            param2: Description of parameter 2
            
        Returns:
            Description of return value
            
        Raises:
            Exception: Description of when exceptions might be raised
        \"\"\"
        # Implement your tool's functionality
        # ...
        # Return the result
```

# Output Format
Return only the Python code for the tool, with no additional text before or after the code.
"""


TEST_TEMPLATE = """
You are an expert in testing Python code. Your task is to create a test suite for the following tool:

# Tool Code
```python
{tool_code}
```

# Test Requirements
- Create pytest functions to test all functionality of the tool
- Include both positive and negative test cases
- Mock external dependencies (APIs, file systems, etc.) to ensure tests are isolated
- Test edge cases and error handling

# Output Format
Return only the Python code for the test module, with no additional text before or after the code.
The test module should follow this structure:

```python
import pytest
from unittest.mock import patch, MagicMock
from autogen_toolsmith.tools.base.tool_base import BaseTool

# Import the tool you're testing 
# (assume it will be available through a relative import when tests run)
from your_tool_module import YourToolName

def test_initialization():
    # Test tool initialization
    tool = YourToolName()
    assert tool.metadata.name == "your_tool_name"
    assert isinstance(tool, BaseTool)
    
def test_successful_run():
    # Test the tool's run method with valid inputs
    
def test_error_handling():
    # Test the tool's error handling
    
# Add more test functions as needed
```
"""


DOCUMENTATION_TEMPLATE = """
You are an expert technical writer. Your task is to create documentation for the following tool:

# Tool Code
```python
{tool_code}
```

# Documentation Requirements
- Start with a clear, concise overview of what the tool does
- Explain all parameters and return values
- Include example usage
- Document any exceptions or error conditions
- Provide context for when and why this tool would be used

# Output Format
Return the documentation in Markdown format.
""" 