"""
Command-line interface for AutoGen Toolsmith.
"""

import argparse
import json
import os
import sys
from typing import List, Optional

from autogen_toolsmith.generator.code_generator import ToolGenerator
from autogen_toolsmith.storage.registry import registry
from autogen_toolsmith.storage.versioning import version_manager


def create_tool_command(args):
    """Create a new tool from a specification."""
    generator = ToolGenerator(openai_api_key=args.api_key, model=args.model)
    
    # Get the tool specification
    spec = ""
    if args.spec_file:
        with open(args.spec_file, 'r') as f:
            spec = f.read()
    else:
        print("Enter tool specification (press Ctrl+D on a new line when done):")
        spec = sys.stdin.read()
    
    if not spec.strip():
        print("Error: Empty tool specification.")
        return 1
    
    # Create the tool
    result = generator.create_tool(spec)
    if result:
        print(f"Tool created successfully: {result}")
        return 0
    else:
        print("Failed to create tool.")
        return 1


def update_tool_command(args):
    """Update an existing tool."""
    generator = ToolGenerator(openai_api_key=args.api_key, model=args.model)
    
    # Get the update specification
    spec = ""
    if args.spec_file:
        with open(args.spec_file, 'r') as f:
            spec = f.read()
    else:
        print("Enter tool update specification (press Ctrl+D on a new line when done):")
        spec = sys.stdin.read()
    
    if not spec.strip():
        print("Error: Empty update specification.")
        return 1
    
    # Update the tool
    result = generator.update_tool(args.tool_name, spec)
    if result:
        print(f"Tool updated successfully: {result}")
        return 0
    else:
        print(f"Failed to update tool {args.tool_name}.")
        return 1


def list_tools_command(args):
    """List all registered tools."""
    tools = registry.list_tools(args.category)
    
    if not tools:
        print("No tools found.")
        return 0
    
    print(f"Found {len(tools)} tools:")
    for i, tool_metadata in enumerate(tools, 1):
        print(f"{i}. {tool_metadata['name']} (v{tool_metadata['version']})")
        print(f"   Description: {tool_metadata['description']}")
        print(f"   Category: {tool_metadata['category']}")
        print(f"   Author: {tool_metadata['author']}")
        if tool_metadata['tags']:
            print(f"   Tags: {', '.join(tool_metadata['tags'])}")
        print()
    
    return 0


def show_tool_command(args):
    """Show details of a specific tool."""
    tool = registry.get_tool(args.tool_name)
    if not tool:
        print(f"Tool {args.tool_name} not found.")
        return 1
    
    tool_dict = tool.to_dict()
    
    print(f"Tool: {tool.metadata.name} (v{tool.metadata.version})")
    print(f"Description: {tool.metadata.description}")
    print(f"Category: {tool.metadata.category}")
    print(f"Author: {tool.metadata.author}")
    if tool.metadata.tags:
        print(f"Tags: {', '.join(tool.metadata.tags)}")
    if tool.metadata.dependencies:
        print(f"Dependencies: {', '.join(tool.metadata.dependencies)}")
    print("\nSignature:")
    print(json.dumps(tool_dict["signature"], indent=2))
    
    if args.show_source:
        source = registry.get_tool_source(args.tool_name)
        if source:
            print("\nSource Code:")
            print(source)
    
    return 0


def get_versions_command(args):
    """Get version history of a tool."""
    versions = version_manager.get_version_history(args.tool_name)
    if not versions:
        print(f"No version history found for tool {args.tool_name}.")
        return 1
    
    print(f"Version history for {args.tool_name}:")
    for i, version in enumerate(versions, 1):
        print(f"{i}. Version {version['version']} (ID: {version['version_id']})")
        print(f"   Created: {version['timestamp']}")
        print(f"   Author: {version['author']}")
        print(f"   Message: {version['commit_message']}")
        print()
    
    return 0


def restore_version_command(args):
    """Restore a specific version of a tool."""
    result = version_manager.restore_version(args.tool_name, args.version_id)
    if result:
        print(f"Tool {args.tool_name} restored to version {args.version_id}.")
        print(f"Restored file: {result}")
        return 0
    else:
        print(f"Failed to restore tool {args.tool_name} to version {args.version_id}.")
        return 1


def delete_tool_command(args):
    """Delete a tool."""
    if registry.remove_tool(args.tool_name):
        print(f"Tool {args.tool_name} deleted successfully.")
        return 0
    else:
        print(f"Failed to delete tool {args.tool_name}.")
        return 1


def main():
    """Main entry point for the autogen-toolsmith command."""
    parser = argparse.ArgumentParser(description="AutoGen Toolsmith CLI")
    
    # Global options
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--model", default="gpt-4o", help="Model to use for code generation")
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create tool command
    create_parser = subparsers.add_parser("create", help="Create a new tool")
    create_parser.add_argument("--spec-file", help="File containing the tool specification")
    create_parser.set_defaults(func=create_tool_command)
    
    # Update tool command
    update_parser = subparsers.add_parser("update", help="Update an existing tool")
    update_parser.add_argument("tool_name", help="Name of the tool to update")
    update_parser.add_argument("--spec-file", help="File containing the update specification")
    update_parser.set_defaults(func=update_tool_command)
    
    # List tools command
    list_parser = subparsers.add_parser("list", help="List all registered tools")
    list_parser.add_argument("--category", help="Filter by category")
    list_parser.set_defaults(func=list_tools_command)
    
    # Show tool command
    show_parser = subparsers.add_parser("show", help="Show details of a specific tool")
    show_parser.add_argument("tool_name", help="Name of the tool to show")
    show_parser.add_argument("--show-source", action="store_true", help="Show the source code of the tool")
    show_parser.set_defaults(func=show_tool_command)
    
    # Get versions command
    versions_parser = subparsers.add_parser("versions", help="Get version history of a tool")
    versions_parser.add_argument("tool_name", help="Name of the tool")
    versions_parser.set_defaults(func=get_versions_command)
    
    # Restore version command
    restore_parser = subparsers.add_parser("restore", help="Restore a specific version of a tool")
    restore_parser.add_argument("tool_name", help="Name of the tool")
    restore_parser.add_argument("version_id", help="Version ID to restore")
    restore_parser.set_defaults(func=restore_version_command)
    
    # Delete tool command
    delete_parser = subparsers.add_parser("delete", help="Delete a tool")
    delete_parser.add_argument("tool_name", help="Name of the tool to delete")
    delete_parser.set_defaults(func=delete_tool_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle case where no command is provided
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main()) 