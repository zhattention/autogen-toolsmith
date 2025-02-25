"""
Tools for AutoGen Toolsmith.
"""

from typing import Any, Dict, List, Optional

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

__all__ = ["get_tool", "list_tools", "BaseTool", "FunctionTool", "ClassTool"]
