"""
Version control for tools in the AutoGen Toolsmith system.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from autogen_toolsmith.tools.base.tool_base import BaseTool


class ToolVersionManager:
    """Manager for versioning tools in the AutoGen Toolsmith system."""
    
    def __init__(self, versions_dir: Optional[str] = None):
        """Initialize the version manager.
        
        Args:
            versions_dir: The directory to store version data. Defaults to 'versions' in the package directory.
        """
        if versions_dir is None:
            # Get the package directory
            package_dir = Path(__file__).parent.parent
            versions_dir = package_dir / "storage" / "versions"
        
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(exist_ok=True, parents=True)
    
    def save_version(self, tool: BaseTool, source_code: str, commit_message: str = ""):
        """Save a new version of a tool.
        
        Args:
            tool: The tool to save.
            source_code: The source code of the tool.
            commit_message: A message describing the changes.
            
        Returns:
            str: The version identifier.
        """
        tool_dir = self.versions_dir / tool.metadata.name
        tool_dir.mkdir(exist_ok=True, parents=True)
        
        # Create a version identifier
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version_id = f"{tool.metadata.version}-{timestamp}"
        
        # Save the source code
        source_file = tool_dir / f"{version_id}.py"
        with open(source_file, 'w') as f:
            f.write(source_code)
        
        # Save the metadata
        metadata = tool.to_dict()
        metadata["commit_message"] = commit_message
        metadata["timestamp"] = timestamp
        
        metadata_file = tool_dir / f"{version_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update the version history
        history_file = tool_dir / "history.json"
        history = []
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        history.append({
            "version_id": version_id,
            "version": tool.metadata.version,
            "timestamp": timestamp,
            "commit_message": commit_message,
            "author": tool.metadata.author
        })
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return version_id
    
    def get_version_history(self, tool_name: str) -> List[Dict[str, Any]]:
        """Get the version history for a tool.
        
        Args:
            tool_name: The name of the tool.
            
        Returns:
            List[Dict[str, Any]]: The version history, newest first.
        """
        tool_dir = self.versions_dir / tool_name
        history_file = tool_dir / "history.json"
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            return list(reversed(history))  # Newest first
        
        return []
    
    def get_version(self, tool_name: str, version_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific version of a tool.
        
        Args:
            tool_name: The name of the tool.
            version_id: The version identifier.
            
        Returns:
            Optional[Dict[str, Any]]: The tool metadata and source code.
        """
        tool_dir = self.versions_dir / tool_name
        source_file = tool_dir / f"{version_id}.py"
        metadata_file = tool_dir / f"{version_id}.json"
        
        if source_file.exists() and metadata_file.exists():
            with open(source_file, 'r') as f:
                source_code = f.read()
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            return {
                "metadata": metadata,
                "source_code": source_code
            }
        
        return None
    
    def restore_version(self, tool_name: str, version_id: str) -> Optional[str]:
        """Restore a tool to a specific version.
        
        Args:
            tool_name: The name of the tool.
            version_id: The version identifier.
            
        Returns:
            Optional[str]: The path to the restored tool file, or None if the version doesn't exist.
        """
        version = self.get_version(tool_name, version_id)
        if not version:
            return None
        
        # Get the category from the metadata
        category = version["metadata"]["metadata"]["category"] or "utility_tools"
        if category not in ["data_tools", "api_tools", "utility_tools"]:
            category = "utility_tools"
        
        # Get the package directory
        package_dir = Path(__file__).parent.parent
        category_dir = package_dir / "tools" / "catalog" / category
        
        # Ensure the category directory exists
        category_dir.mkdir(exist_ok=True, parents=True)
        
        # Create an empty __init__.py file if it doesn't exist
        init_file = category_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        
        # Save the source code
        tool_file = category_dir / f"{tool_name}.py"
        with open(tool_file, 'w') as f:
            f.write(version["source_code"])
        
        return str(tool_file)


# Create a global version manager instance
version_manager = ToolVersionManager() 