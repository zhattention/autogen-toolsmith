"""
Tool registry for storing and retrieving tools.
"""

import json
import os
import importlib.util
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, Tuple

from autogen_toolsmith.tools.base.tool_base import BaseTool


class ToolRegistry:
    """Registry for managing tools in the AutoGen Toolsmith system."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the tool registry.
        
        Args:
            storage_dir: The directory to store tool data. Defaults to the 'tools/catalog' directory.
        """
        if storage_dir is None:
            # Get the package directory
            package_dir = Path(__file__).parent.parent
            storage_dir = package_dir / "tools" / "catalog"
        
        self.storage_dir = Path(storage_dir)
        self.tools: Dict[str, BaseTool] = {}
        self.tool_index: Dict[str, Dict[str, Any]] = {}
        self._load_tools()
    
    def _load_tools(self):
        """Load all tools from the storage directory."""
        self.tools = {}
        self.tool_index = {}
        
        # Ensure category directories exist
        for category in ["data_tools", "api_tools", "utility_tools"]:
            category_dir = self.storage_dir / category
            category_dir.mkdir(exist_ok=True, parents=True)
            
            # Create an empty __init__.py file if it doesn't exist
            init_file = category_dir / "__init__.py"
            if not init_file.exists():
                init_file.touch()
            
            # Check for tool modules in this category
            for tool_file in category_dir.glob("*.py"):
                if tool_file.name == "__init__.py":
                    continue
                
                try:
                    # Load the module
                    module_name = f"autogen_toolsmith.tools.catalog.{category}.{tool_file.stem}"
                    spec = importlib.util.spec_from_file_location(module_name, tool_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Find tool classes in the module
                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj) 
                                and issubclass(obj, BaseTool) 
                                and obj is not BaseTool
                            ):
                                # Instantiate the tool
                                tool_instance = obj()
                                self._register_tool(tool_instance)
                except Exception as e:
                    print(f"Error loading tool from {tool_file}: {e}")
    
    def _register_tool(self, tool: BaseTool):
        """Register a tool with the registry."""
        if tool.metadata.name in self.tools:
            # If the tool already exists, only register the newer version
            existing_tool = self.tools[tool.metadata.name]
            if existing_tool.metadata.version < tool.metadata.version:
                self.tools[tool.metadata.name] = tool
                self.tool_index[tool.metadata.name] = tool.to_dict()
        else:
            self.tools[tool.metadata.name] = tool
            self.tool_index[tool.metadata.name] = tool.to_dict()
    
    def verify_dependencies(self, tool: BaseTool) -> Tuple[bool, Optional[str]]:
        """Verify that all dependencies of a tool are available in the registry.
        
        Args:
            tool: The tool to verify dependencies for.
            
        Returns:
            Tuple[bool, Optional[str]]: A tuple of (dependencies_satisfied, error_message).
        """
        if not tool.metadata.dependencies:
            return True, None
        
        missing_dependencies = []
        for dependency_name in tool.metadata.dependencies:
            if dependency_name not in self.tools:
                missing_dependencies.append(dependency_name)
        
        if missing_dependencies:
            return False, f"Missing dependencies: {', '.join(missing_dependencies)}"
        
        return True, None
    
    def register(self, tool: BaseTool) -> bool:
        """Register a tool with the registry.
        
        Args:
            tool: The tool to register.
            
        Returns:
            bool: True if registration was successful, False otherwise.
        """
        try:
            # Verify dependencies first
            deps_satisfied, error_msg = self.verify_dependencies(tool)
            if not deps_satisfied:
                print(f"Warning: {error_msg}")
                # We still register the tool, but print a warning
            
            self._register_tool(tool)
            
            # Determine the category directory
            category = tool.metadata.category or "utility_tools"
            if category not in ["data_tools", "api_tools", "utility_tools"]:
                category = "utility_tools"
            
            category_dir = self.storage_dir / category
            category_dir.mkdir(exist_ok=True, parents=True)
            
            # Create an empty __init__.py file if it doesn't exist
            init_file = category_dir / "__init__.py"
            if not init_file.exists():
                init_file.touch()
            
            # Update the tool index file
            index_file = self.storage_dir / "tool_index.json"
            with open(index_file, 'w') as f:
                json.dump(self.tool_index, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error registering tool {tool.metadata.name}: {e}")
            return False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: The name of the tool to get.
            
        Returns:
            Optional[BaseTool]: The tool, or None if it doesn't exist.
        """
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered tools.
        
        Args:
            category: Filter by category.
            
        Returns:
            List[Dict[str, Any]]: List of tool metadata.
        """
        if not category:
            return [t.to_dict()["metadata"] for t in self.tools.values()]
        return [
            t.to_dict()["metadata"] for t in self.tools.values() 
            if t.metadata.category == category
        ]
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool from the registry.
        
        Args:
            name: The name of the tool to remove.
            
        Returns:
            bool: True if removal was successful, False otherwise.
        """
        if name in self.tools:
            tool = self.tools[name]
            category = tool.metadata.category or "utility_tools"
            if category not in ["data_tools", "api_tools", "utility_tools"]:
                category = "utility_tools"
            
            # Remove the tool from memory
            del self.tools[name]
            del self.tool_index[name]
            
            # Remove the tool's Python file
            tool_file = self.storage_dir / category / f"{name}.py"
            if tool_file.exists():
                tool_file.unlink()
            
            # Update the tool index file
            index_file = self.storage_dir / "tool_index.json"
            with open(index_file, 'w') as f:
                json.dump(self.tool_index, f, indent=2)
            
            return True
        
        return False
    
    def get_tool_source(self, name: str) -> Optional[str]:
        """Get the source code for a tool.
        
        Args:
            name: The name of the tool.
            
        Returns:
            Optional[str]: The source code, or None if the tool doesn't exist.
        """
        if name in self.tools:
            tool = self.tools[name]
            category = tool.metadata.category or "utility_tools"
            if category not in ["data_tools", "api_tools", "utility_tools"]:
                category = "utility_tools"
            
            # Get the tool's Python file
            tool_file = self.storage_dir / category / f"{name}.py"
            if tool_file.exists():
                with open(tool_file, 'r') as f:
                    return f.read()
        
        return None


# Create a global registry instance
registry = ToolRegistry()

def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool by name.
    
    Args:
        name: The name of the tool to get.
        
    Returns:
        Optional[BaseTool]: The tool, or None if it doesn't exist.
    """
    return registry.get_tool(name)

def list_tools(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all registered tools.
    
    Args:
        category: Filter by category.
        
    Returns:
        List[Dict[str, Any]]: List of tool metadata.
    """
    return registry.list_tools(category) 