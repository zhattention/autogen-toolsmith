"""
Prompt templates for code generation.
"""

TOOL_TEMPLATE = """
You are an expert in developing Python tools for the AutoGen framework. Your task is to create a new tool based on the following specification:

# Tool Specification
{tool_specification}

# Available Dependencies
The tool can leverage the following existing tools as dependencies:
{available_dependencies}

## How to Use Existing Tools as Dependencies
To use an existing tool as a dependency:

1. Add the tool name to the dependencies list in the constructor:
   ```python
   super().__init__(
       name="your_tool_name",
       description="A brief description",
       dependencies=["existing_tool_name"],  # List dependent tools here
       # other parameters...
   )
   ```

2. Import and use the tool in your code:
   ```python
   from autogen_toolsmith.tools import get_tool
   
   def run(self, ...):
       # Get the dependent tool
       existing_tool = get_tool("existing_tool_name")
       if existing_tool is None:
           raise ValueError("Required dependency 'existing_tool_name' not found")
           
       # Use the dependent tool
       result = existing_tool.run(...)
       
       # Process the result and continue with your implementation
       # ...
   ```

# Code Format Requirements
- Create a Python class that inherits from BaseTool
- The class should have a descriptive name ending with "Tool"
- Implement a `run` method with appropriate parameters based on the specification
- Include proper typing and documentation
- Handle errors gracefully, especially when dependent tools might fail
- Include example usage in docstrings
- Make sure all arguments to the constructor and run method are validated

# Tool Class Structure
The tool should follow this structure:

```python
from typing import Any, Dict, List, Optional
from autogen_toolsmith.tools.base.tool_base import BaseTool
from autogen_toolsmith.tools import get_tool  # Import this to use dependent tools

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
        # If you're using dependent tools, get them here
        # dependent_tool = get_tool("dependent_tool_name")
        # if dependent_tool is None:
        #     raise ValueError("Required dependency 'dependent_tool_name' not found")
        
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
- If the tool uses other tools as dependencies, mock those dependencies

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
    
# If the tool has dependencies on other tools, mock them like this:
@patch('autogen_toolsmith.tools.get_tool')
def test_with_dependencies(mock_get_tool):
    # Setup mock for dependent tool
    mock_dependent_tool = MagicMock()
    mock_dependent_tool.run.return_value = "expected result"
    mock_get_tool.return_value = mock_dependent_tool
    
    # Test your tool using the mock
    tool = YourToolName()
    result = tool.run(...)
    
    # Assert dependencies were called correctly
    mock_get_tool.assert_called_once_with("dependent_tool_name")
    mock_dependent_tool.run.assert_called_once_with(...)
    
    # Assert the result
    assert result == "expected result after processing"
    
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
- Document any dependencies on other tools and how they're used
- Document any exceptions or error conditions
- Provide context for when and why this tool would be used

# Output Format
Return the documentation in Markdown format.
""" 