# AutoGen Toolsmith

A Python library for automatically generating, testing, and managing tools for AI agents.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![AutoGen](https://img.shields.io/badge/AutoGen-0.4.0%2B-green)

## 🚀 Overview

AutoGen Toolsmith is a powerful framework that dramatically improves the efficiency of creating tools for AI agents. It serves as:

1. **A Tool Creation Accelerator**: Generate fully functional tools from natural language descriptions in minutes
2. **A Foundation for Agent Capabilities**: Build the essential building blocks that determine what agents can do
3. **A Framework-Agnostic Solution**: Easily integrate with AutoGen, LangChain, CrewAI and other agent frameworks
4. **An MCP Protocol Compatible System**: Support standardized communication in multi-agent systems
5. **A Curated Tool Repository**: Access pre-built tools for common tasks like web search, web scraping, and document processing

## 🔧 Installation

```bash
pip install autogen-toolsmith
```

## 🏁 Quick Start

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

## ✨ Key Features

### 🛠️ Efficient Tool Creation

- Generate tools from natural language descriptions
- Automatic test generation and validation
- Built-in security checks
- Comprehensive documentation generation

### 🔄 Tool Dependency Management

- Create tools that leverage existing tools
- Automatic dependency tracking and validation
- Build complex tool chains with simple descriptions

### 🔌 Framework Integration

- Native support for AutoGen agents
- Easy adapters for other frameworks
- Consistent interfaces across all tools

### 📚 Pre-built Tool Library

- Web interaction tools (search, scraping)
- Document processing tools
- Data analysis utilities
- API integrations
- And many more!

## 📖 Documentation

For complete documentation, visit our [documentation site](https://github.com/yourusername/autogen-toolsmith/docs).

- [Getting Started Guide](docs/getting_started.md)
- [Tool Creation Tutorial](docs/tool_creation.md)
- [API Reference](docs/api_reference.md)
- [Project Vision](docs/project_vision.md)

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/contributing.md) for more information.

## 📄 License

MIT 