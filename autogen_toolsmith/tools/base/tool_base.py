"""
Base classes for all tools in the AutoGen Toolsmith system.
"""

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    description: str
    version: str
    created_at: datetime
    updated_at: datetime
    author: str
    dependencies: List[str] = None
    tags: List[str] = None
    category: str = None


class BaseTool(ABC):
    """Base class for all tools in the AutoGen Toolsmith system."""

    def __init__(self, name: str, description: str, version: str = "0.1.0", 
                 author: str = "AutoGen Toolsmith", dependencies: List[str] = None,
                 tags: List[str] = None, category: str = None):
        """Initialize a tool with metadata.
        
        Args:
            name: The name of the tool.
            description: A description of what the tool does.
            version: The version of the tool.
            author: The author of the tool.
            dependencies: A list of other tools this tool depends on.
            tags: Tags to categorize this tool.
            category: The category this tool belongs to.
        """
        self.metadata = ToolMetadata(
            name=name,
            description=description,
            version=version,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            author=author,
            dependencies=dependencies or [],
            tags=tags or [],
            category=category or "uncategorized"
        )
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Run the tool with the given arguments."""
        pass
    
    def get_signature(self) -> Dict[str, Any]:
        """Get the signature of the tool's run method."""
        sig = inspect.signature(self.run)
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "parameters": {
                name: {
                    "type": param.annotation.__name__ if param.annotation is not inspect.Parameter.empty else "Any",
                    "description": "",  # Would be populated from docstring
                    "default": None if param.default is inspect.Parameter.empty else param.default
                }
                for name, param in sig.parameters.items()
                if name != "self"
            },
            "returns": sig.return_annotation.__name__ if sig.return_annotation is not inspect.Parameter.empty else "Any"
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tool to a dictionary for serialization."""
        return {
            "metadata": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "version": self.metadata.version,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "author": self.metadata.author,
                "dependencies": self.metadata.dependencies,
                "tags": self.metadata.tags,
                "category": self.metadata.category
            },
            "signature": self.get_signature()
        }


class FunctionTool(BaseTool):
    """A tool that wraps a function."""
    
    def __init__(self, func: Callable, name: str = None, description: str = None, 
                 version: str = "0.1.0", author: str = "AutoGen Toolsmith",
                 dependencies: List[str] = None, tags: List[str] = None, 
                 category: str = None):
        """Initialize a function tool.
        
        Args:
            func: The function to wrap.
            name: The name of the tool (defaults to function name).
            description: A description of what the tool does (defaults to function docstring).
            version: The version of the tool.
            author: The author of the tool.
            dependencies: A list of other tools this tool depends on.
            tags: Tags to categorize this tool.
            category: The category this tool belongs to.
        """
        self.func = func
        name = name or func.__name__
        description = description or (func.__doc__ or f"Executes the {func.__name__} function.")
        super().__init__(name, description, version, author, dependencies, tags, category)
    
    def run(self, *args, **kwargs) -> Any:
        """Run the wrapped function with the given arguments."""
        return self.func(*args, **kwargs)
    
    def get_signature(self) -> Dict[str, Any]:
        """Get the signature of the wrapped function."""
        sig = inspect.signature(self.func)
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "parameters": {
                name: {
                    "type": param.annotation.__name__ if param.annotation is not inspect.Parameter.empty else "Any",
                    "description": "",  # Would need to parse from docstring
                    "default": None if param.default is inspect.Parameter.empty else param.default
                }
                for name, param in sig.parameters.items()
            },
            "returns": sig.return_annotation.__name__ if sig.return_annotation is not inspect.Parameter.empty else "Any"
        }


class ClassTool(BaseTool):
    """A tool that wraps a class instance's methods."""
    
    def __init__(self, instance: Any, method_name: str, name: str = None, 
                 description: str = None, version: str = "0.1.0", 
                 author: str = "AutoGen Toolsmith", dependencies: List[str] = None,
                 tags: List[str] = None, category: str = None):
        """Initialize a class tool.
        
        Args:
            instance: The class instance to wrap.
            method_name: The name of the method to call when run is called.
            name: The name of the tool (defaults to class name + method name).
            description: A description of what the tool does (defaults to method docstring).
            version: The version of the tool.
            author: The author of the tool.
            dependencies: A list of other tools this tool depends on.
            tags: Tags to categorize this tool.
            category: The category this tool belongs to.
        """
        self.instance = instance
        self.method_name = method_name
        self.method = getattr(instance, method_name)
        
        name = name or f"{instance.__class__.__name__}_{method_name}"
        description = description or (self.method.__doc__ or f"Executes the {method_name} method of {instance.__class__.__name__}.")
        super().__init__(name, description, version, author, dependencies, tags, category)
    
    def run(self, *args, **kwargs) -> Any:
        """Run the wrapped method with the given arguments."""
        return self.method(*args, **kwargs)
    
    def get_signature(self) -> Dict[str, Any]:
        """Get the signature of the wrapped method."""
        sig = inspect.signature(self.method)
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "parameters": {
                name: {
                    "type": param.annotation.__name__ if param.annotation is not inspect.Parameter.empty else "Any",
                    "description": "",  # Would need to parse from docstring
                    "default": None if param.default is inspect.Parameter.empty else param.default
                }
                for name, param in sig.parameters.items()
                if name != "self"  # Skip the self parameter
            },
            "returns": sig.return_annotation.__name__ if sig.return_annotation is not inspect.Parameter.empty else "Any"
        } 