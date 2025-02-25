# AutoGen Toolsmith

A Python library for automatically generating, testing, and managing tools for AutoGen agents.

## Overview

AutoGen Toolsmith simplifies the process of creating and managing tools that can be used by agents in the AutoGen framework. This library allows you to:

- Generate tool code based on natural language descriptions
- Automatically test generated tools to ensure functionality
- Maintain a registry of available tools
- Allow new tools to leverage existing tools as dependencies
- Provide easy-to-use interfaces for agents to discover and use tools

## Installation

```bash
pip install autogen-toolsmith
```

## Quick Start

```python
from autogen_toolsmith import ToolGenerator

# Initialize the tool generator
generator = ToolGenerator()

# Generate a new tool from a description
tool_spec = """
Create a tool that can fetch weather data for a given location.
The tool should take a city name and return current temperature and conditions.
"""

# Generate, test and register the tool
tool_path = generator.create_tool(tool_spec)

# The tool is now available in your tool registry
from autogen_toolsmith.tools import get_tool

weather_tool = get_tool("weather_fetcher")
result = weather_tool.run("New York")
print(result)
```

## Features

- **Natural Language Tool Creation**: Describe the tool you need, and let the generator create it
- **Automatic Testing**: Generated tools are automatically tested before being added to the registry
- **Tool Registry**: Easily discover and use available tools
- **Tool Dependencies**: New tools can build upon existing tools
- **Version Control**: Track changes to tools over time

## License

MIT 