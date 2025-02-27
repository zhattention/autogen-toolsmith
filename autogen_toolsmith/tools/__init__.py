"""
Tools for AutoGen Toolsmith.
"""

from typing import Any, Dict, List, Optional, Callable

# 移除循环导入
# from autogen_toolsmith.storage.registry import get_tool, list_tools
from autogen_toolsmith.tools.base.tool_base import BaseTool, FunctionTool, ClassTool

# 创建转发函数而不是直接导入
def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool by name.
    
    Args:
        name: The name of the tool to get.
        
    Returns:
        Optional[BaseTool]: The tool, or None if it doesn't exist.
    """
    from autogen_toolsmith.storage.registry import get_tool as _get_tool
    return _get_tool(name)

def list_tools(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all registered tools.
    
    Args:
        category: Filter by category.
        
    Returns:
        List[Dict[str, Any]]: List of tool metadata.
    """
    from autogen_toolsmith.storage.registry import list_tools as _list_tools
    return _list_tools(category)

def get_all_tools_as_functions(category: Optional[str] = None) -> List[Callable]:
    """Get all registered tools converted to callable functions suitable for AutoGen agents.
    
    This function returns all registered tools (or tools from a specific category)
    converted to standalone functions that can be directly used with AutoGen agents.
    
    Args:
        category: Optional category to filter tools by. If None, returns all tools.
        
    Returns:
        List[Callable]: List of callable functions that wrap the tools.
    """
    from autogen_toolsmith.storage.registry import registry
    tools_list = []
    
    # Get all tools or filter by category
    all_tools = registry.tools.values()
    if category:
        all_tools = [t for t in all_tools if t.metadata.category == category]
    
    # Convert each tool to a function
    for tool in all_tools:
        # Use the helper function to create a tool function
        tools_list.append(make_tool_function(tool))
    
    return tools_list

def enumerate_tools(categories: Optional[List[str]] = None) -> Dict[str, List[Callable]]:
    """Enumerate all tools by category and convert them to callable functions.
    
    This function returns all registered tools organized by category and
    converted to functions that can be directly used with AutoGen agents.
    
    Args:
        categories: Optional list of categories to include. If None, returns all categories.
        
    Returns:
        Dict[str, List[Callable]]: Dictionary with categories as keys and lists of callable functions as values.
    """
    from autogen_toolsmith.storage.registry import registry
    
    # Get all available categories from registered tools
    all_categories = set(tool.metadata.category for tool in registry.tools.values() 
                        if tool.metadata.category is not None)
    
    # Filter categories if specified
    if categories:
        all_categories = [cat for cat in all_categories if cat in categories]
    
    # Organize tools by category
    result = {}
    for category in all_categories:
        result[category] = get_all_tools_as_functions(category)
    
    # Add uncategorized tools
    uncategorized = [tool for tool in registry.tools.values() 
                    if tool.metadata.category is None or tool.metadata.category not in all_categories]
    if uncategorized:
        result["uncategorized"] = [make_tool_function(tool) for tool in uncategorized]
    
    return result

def make_tool_function(tool_instance):
    """Helper function to convert a tool instance to a callable function.
    
    Args:
        tool_instance: The BaseTool instance to convert.
        
    Returns:
        Callable: A function that wraps the tool's run method.
    """
    # Create the wrapper function with the tool's docstring
    def tool_function(*args, **kwargs):
        """Tool function wrapper."""
        result = tool_instance.run(*args, **kwargs)
        return result
    
    # Set the function name and docstring
    tool_function.__name__ = tool_instance.metadata.name
    tool_function.__doc__ = tool_instance.metadata.description
    
    return tool_function

__all__ = ["get_tool", "list_tools", "BaseTool", "FunctionTool", "ClassTool",
           "get_all_tools_as_functions", "enumerate_tools"]
