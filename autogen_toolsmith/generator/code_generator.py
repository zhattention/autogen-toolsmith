"""
Code generator for creating tools in the AutoGen Toolsmith system.
"""

import importlib
import inspect
import json
import os
import re
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest

from autogen_toolsmith.generator.code_validator import CodeValidator
from autogen_toolsmith.generator.prompt_templates import TOOL_TEMPLATE, TEST_TEMPLATE, DOCUMENTATION_TEMPLATE, UPDATE_TEMPLATE, UPDATE_WITH_TEST_RESULTS_TEMPLATE
from autogen_toolsmith.storage.registry import registry, init_registry
from autogen_toolsmith.storage.versioning import version_manager
from autogen_toolsmith.tools.base.tool_base import BaseTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_toolsmith.tools import get_tool

class ToolGenerator:
    """Generator for creating and updating tools in the AutoGen Toolsmith system."""
    
    def __init__(
        self,
        model_client: Optional[OpenAIChatCompletionClient] = None,
        storage_dirs: Optional[List[str]] = None,
    ):
        """Initialize the tool generator.
        
        Args:
            model_client: The model client to use for code generation.
                        If None, only tool listing and retrieval functions will work.
            storage_dirs: List of directories to store and load tool data.
                        If None, uses the default directory.
        """
        self.model_client = model_client
        
        # Initialize registry with storage directories if provided
        if storage_dirs:
            init_registry(storage_dirs)
        
        self.validator = CodeValidator()
    
    async def _generate_code(self, prompt: str) -> str:
        """Generate code using the model client.
        
        Args:
            prompt: The prompt to use for code generation.
            
        Returns:
            str: The generated code.
            
        Raises:
            ValueError: If no model client is provided.
        """
        if self.model_client is None:
            raise ValueError("Model client is required for code generation. Please provide a model_client when initializing ToolGenerator.")
            
        from autogen_core.models import SystemMessage, UserMessage
        
        response = await self.model_client.create(
            messages=[
                SystemMessage(
                    content="You are an expert code generator for Python tools. Respond with only the code, no explanations.",
                    source="system"
                ),
                UserMessage(
                    content=prompt,
                    source="user"
                )
            ],
            extra_create_args={
                "temperature": 0.2
            }
        )
        
        # 处理返回结果 - 根据新的model_client接口提取内容
        if hasattr(response, 'content'):
            if isinstance(response.content, str):
                return response.content
        
        # 如果无法提取内容，抛出异常
        raise ValueError(f"Unable to extract content from model response: {response}")
    
    def _extract_code_block(self, text: str) -> str:
        """Extract code block from text.
        
        Args:
            text: The text containing code blocks.
            
        Returns:
            str: The extracted code block, or the original text if no code block is found.
        """
        # Try to extract Python code blocks
        python_blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
        if python_blocks:
            return python_blocks[0].strip()
        
        # Try to extract generic code blocks
        generic_blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
        if generic_blocks:
            return generic_blocks[0].strip()
        
        # Return the original text if no code blocks are found
        return text.strip()
    
    def _get_available_dependencies(self) -> str:
        """Get a string representation of available dependencies (existing tools).
        
        Returns:
            str: A formatted string of available dependencies.
        """
        tools = registry.list_tools()
        if not tools:
            return "No existing tools available."
        
        dependencies_text = "## Existing Tools\n"
        for tool_metadata in tools:
            tool_name = tool_metadata['name']
            tool = registry.get_tool(tool_name)
            
            dependencies_text += f"### {tool_metadata['name']}\n"
            dependencies_text += f"- **Description**: {tool_metadata['description']}\n"
            dependencies_text += f"- **Category**: {tool_metadata.get('category', 'utility_tools')}\n"
            
            # 获取工具的运行方法详情
            if tool:
                try:
                    # 获取run方法的签名和文档
                    import inspect
                    
                    run_method = getattr(tool, 'run', None)
                    if run_method and callable(run_method):
                        # 提取参数信息
                        sig = inspect.signature(run_method)
                        params = []
                        for name, param in sig.parameters.items():
                            if name == 'self':
                                continue
                            param_str = name
                            if param.annotation != inspect.Parameter.empty:
                                param_type = str(param.annotation)
                                param_type = param_type.replace('typing.', '').replace('<class \'', '').replace('\'>', '')
                                param_str += f": {param_type}"
                            if param.default != inspect.Parameter.empty:
                                default_val = repr(param.default)
                                param_str += f" = {default_val}"
                            params.append(param_str)
                        
                        # 添加方法签名
                        dependencies_text += f"- **Usage**: `{tool_name}.run({', '.join(params)})`\n"
                        
                        # 添加文档说明
                        if run_method.__doc__:
                            doc = inspect.getdoc(run_method)
                            dependencies_text += f"- **Documentation**:\n```\n{doc}\n```\n"
                except Exception as e:
                    # 如果分析工具方法出错，只记录基本信息
                    dependencies_text += f"- **Usage**: See tool documentation for details.\n"
            
            dependencies_text += "\n"
        
        return dependencies_text
    
    def _get_existing_tools_info(self) -> str:
        """Get information about existing tools for reuse.
        
        Returns:
            str: A formatted string with information about existing tools.
        """
        tools_info = "# Available Tools for Reuse\n"
        
        # Get all registered tools
        all_tools = registry.list_tools()
        
        if not all_tools:
            return "# No existing tools available for reuse\n"
        
        # Group tools by category
        tools_by_category = {}
        for tool_data in all_tools:
            category = tool_data.get("metadata", {}).get("category", "uncategorized")
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool_data)
        
        # Format the tools information
        for category, tools in tools_by_category.items():
            tools_info += f"\n## {category.replace('_', ' ').title()}\n"
            
            for tool_data in tools:
                metadata = tool_data.get("metadata", {})
                signature = tool_data.get("signature", {})
                
                name = metadata.get("name", "unknown")
                description = metadata.get("description", "No description")
                
                tools_info += f"- **{name}**: {description}\n"
                
                # Add parameters information if available
                parameters = signature.get("parameters", {})
                if parameters:
                    tools_info += "  - Parameters:\n"
                    for param_name, param_info in parameters.items():
                        param_type = param_info.get("type", "Any")
                        param_desc = param_info.get("description", "")
                        tools_info += f"    - `{param_name}` ({param_type}): {param_desc}\n"
                
                # Add return information if available
                returns = signature.get("returns", "Any")
                tools_info += f"  - Returns: {returns}\n"
                
                # Add import information
                category_path = metadata.get("category", "utility_tools")
                tools_info += f"  - Import: `from autogen_toolsmith.tools.catalog.{category_path}.{name} import {name.title().replace('_', '')}Tool`\n"
        
        return tools_info
    
    async def create_tool(
        self, 
        specification: str, 
        output_dir: Optional[str] = None,
        register: bool = True
    ) -> Optional[str]:
        """Create a new tool based on the specification.
        
        Args:
            specification: The tool specification.
            output_dir: Optional directory to store the tool.
                       If None, uses "./tools" directory.
            register: Whether to register the tool in the registry.
            
        Returns:
            Optional[str]: The tool name if successful, None otherwise.
        """
        # Set default output directory if none is provided
        if output_dir is None:
            output_dir = "./tools"
            os.makedirs(output_dir, exist_ok=True)
            
        # Get available dependencies and existing tools information
        available_dependencies = self._get_available_dependencies()
        existing_tools_info = self._get_existing_tools_info()
        
        # Generate tool code with information about existing tools
        tool_prompt = TOOL_TEMPLATE.format(
            specification=specification,
            existing_tools_info=existing_tools_info
        )
        tool_code_raw = await self._generate_code(tool_prompt)

        # save the tool_code_raw to a debug file
        with open("tool_code_raw.txt", "a") as f:
            f.write(tool_code_raw)
        
        # Extract and validate the tool code
        tool_code = self._extract_code_block(tool_code_raw)
        if not tool_code:
            print("Error: Could not extract valid Python code from the generated tool code.")
            return None
        
        # Get tool metadata
        tool_metadata = self._extract_tool_metadata(tool_code)
        if not tool_metadata:
            print("Error: Could not extract tool metadata from the generated code.")
            return None
        
        # Generate test code
        test_prompt = TEST_TEMPLATE.format(
            tool_name=tool_metadata["name"],
            tool_code=tool_code,
            test_results="",
            current_test_code="",
            tool_dir=output_dir or "./tools"
        )
        test_code_raw = await self._generate_code(test_prompt)
        test_code = self._extract_code_block(test_code_raw)
        
        # Generate documentation
        doc_prompt = DOCUMENTATION_TEMPLATE.format(
            tool_name=tool_metadata["name"],
            tool_code=tool_code
        )
        doc_raw = await self._generate_code(doc_prompt)
        doc = self._extract_code_block(doc_raw)
        
        # Validate the generated code
        if not self.validator.validate_tool(tool_code):
            print("Error: Generated tool code failed validation.")
            return None
        
        if not self.validator.validate_test(test_code):
            print("Error: Generated test code failed validation.")
            return None
        
        # Create tool instance and register if requested
        tool_instance = self._create_tool_instance(tool_code)
        if not tool_instance:
            print("Error: Could not create tool instance from generated code.")
            return None
        
        if register:
            # 确保目录存在
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 使用指定的output_dir注册工具
            if not registry.register(tool_instance, output_dir):
                print("Error: Failed to register tool.")
                return None
                
            # 提示用户如何使用指定目录获取工具
            if output_dir:
                print(f"Tool registered in custom directory: {output_dir}")
                print(f"To use this tool, call: get_tool('{tool_metadata['name']}', storage_dir='{output_dir}')")
            
        # Save test code to file if output_dir is provided
        if output_dir:
            # Use the same directory structure as the tool
            test_dir = os.path.join(output_dir, tool_metadata["category"], "tests")
            # Create the test directory if it doesn't exist
            os.makedirs(test_dir, exist_ok=True)
            # Save the test code
            test_file_path = os.path.join(test_dir, f"test_{tool_metadata['name']}.py")
            with open(test_file_path, "w") as f:
                f.write(test_code)
            print(f"Test code saved to {test_file_path}")
        
        # Return the tool name instead of file path for easier tool calling
        return tool_metadata["name"]
        

    async def update_tool(
        self, 
        tool_name: str, 
        update_specification: str,
        output_dir: Optional[str] = None,
        register: bool = True
    ) -> Optional[str]:
        """Update an existing tool based on the update specification.
        
        Args:
            tool_name: The name of the tool to update.
            update_specification: The update specification.
            output_dir: Optional directory to store the updated tool.
                       If None, uses "./tools" directory.
            register: Whether to register the updated tool.
            
        Returns:
            Optional[str]: The tool name if successful, None otherwise.
        """
        try:
            # Set default output directory if none is provided
            if output_dir is None:
                output_dir = "./tools"
                os.makedirs(output_dir, exist_ok=True)
                
            # Get the existing tool
            tool = get_tool(tool_name, storage_dir=output_dir)
            if not tool:
                print(f"Error: Tool '{tool_name}' not found.")
                return None
            
            # Generate updated code
            update_prompt = UPDATE_TEMPLATE.format(
                tool_name=tool_name,
                existing_code=tool.get_source(),
                update_specification=update_specification
            )
            updated_code_raw = await self._generate_code(update_prompt)
            updated_code = self._extract_code_block(updated_code_raw)
            
            if not updated_code:
                print("Error: Could not extract valid Python code from the generated update.")
                return None
            
            # Generate updated test code
            test_prompt = TEST_TEMPLATE.format(
                tool_name=tool_name,
                tool_code=updated_code,
                tool_dir=output_dir or "./tools"
            )
            test_code_raw = await self._generate_code(test_prompt)
            test_code = self._extract_code_block(test_code_raw)
            
            # Generate updated documentation
            doc_prompt = DOCUMENTATION_TEMPLATE.format(
                tool_name=tool_name,
                tool_code=updated_code
            )
            doc_raw = await self._generate_code(doc_prompt)
            doc = self._extract_code_block(doc_raw)
            
            # Validate the updated code
            if not self.validator.validate_tool(updated_code):
                print("Error: Updated tool code failed validation.")
                return None
            
            if not self.validator.validate_test(test_code):
                print("Error: Updated test code failed validation.")
                return None
            
            # Create updated tool instance and register if requested
            updated_tool = self._create_tool_instance(updated_code)
            if not updated_tool:
                print("Error: Could not create tool instance from updated code.")
                return None
            
            if register:
                # 确保目录存在
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                
                # Remove the old tool first, passing the storage_dir parameter
                registry.remove_tool(tool_name, storage_dir=output_dir)
                
                # Register the updated tool with specified output_dir
                if not registry.register(updated_tool, output_dir):
                    print("Error: Failed to register updated tool.")
                    return None
                    
                # 提示用户如何使用指定目录获取更新后的工具
                if output_dir:
                    print(f"Tool updated in custom directory: {output_dir}")
                    print(f"To use this tool, call: get_tool('{tool_name}', storage_dir='{output_dir}')")
            
            # Save updated test code to file if output_dir is provided
            if output_dir:
                # Use the same directory structure as the tool
                test_dir = os.path.join(output_dir, updated_tool.metadata.category, "tests")
                # Create the test directory if it doesn't exist
                os.makedirs(test_dir, exist_ok=True)
                # Save the test code
                test_file_path = os.path.join(test_dir, f"test_{tool_name}.py")
                with open(test_file_path, "w") as f:
                    f.write(test_code)
                print(f"Updated test code saved to {test_file_path}")
            
            # Return the tool name instead of file path for easier tool calling
            return tool_name
            
        except Exception as e:
            print(f"Error updating tool: {e}")
            return None
    
    
    def _extract_tool_metadata(self, code: str) -> Optional[Dict[str, str]]:
        """Extract tool metadata from the generated code.
        
        Args:
            code: The generated tool code.
            
        Returns:
            Optional[Dict[str, str]]: The extracted metadata, or None if extraction failed.
        """
        try:
            # Extract the tool name
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', code)
            if not name_match:
                return None
            
            tool_name = name_match.group(1)
            
            # Extract the category
            category_match = re.search(r'category\s*=\s*["\']([^"\']+)["\']', code)
            category = category_match.group(1) if category_match else "utility_tools"
            
            if category not in ["data_tools", "api_tools", "utility_tools"]:
                category = "utility_tools"
            
            # Extract the description
            description_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', code)
            description = description_match.group(1) if description_match else ""
            
            # Extract the version
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', code)
            version = version_match.group(1) if version_match else "0.1.0"
            
            return {
                "name": tool_name,
                "category": category,
                "description": description,
                "version": version
            }
        except Exception as e:
            print(f"Error extracting tool metadata: {e}")
            return None
    
    def _create_tool_instance(self, code: str) -> Optional[BaseTool]:
        """Create a tool instance from the generated code.
        
        Args:
            code: The generated tool code.
            
        Returns:
            Optional[BaseTool]: The created tool instance, or None if creation failed.
        """
        try:
            # Extract the class name
            class_match = re.search(r"class\s+(\w+)\(BaseTool\)", code)
            if not class_match:
                print("Could not extract tool class name.")
                return None
            
            tool_class_name = class_match.group(1)
            
            # Create a temporary module
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
                temp_file.write(code.encode())
                temp_file_path = temp_file.name
            
            try:
                # Import the temporary module
                spec = importlib.util.spec_from_file_location("temp_tool_module", temp_file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Get the tool class
                    tool_class = getattr(module, tool_class_name)
                    
                    # Create an instance of the tool
                    tool_instance = tool_class()
                    
                    # 存储工具的原始元数据，用于后续文件路径构建
                    tool_name = tool_instance.metadata.name
                    tool_category = tool_instance.metadata.category
                    
                    # 修改get_source方法，使其从文件读取源码
                    def get_source(self):
                        """Get the source code of the tool from its file.
                        
                        Returns:
                            str: The source code of the tool.
                        """
                        try:
                            # 尝试使用注册表存储的位置找到工具文件
                            from autogen_toolsmith.storage.registry import registry
                            tool_info = registry.get_tool_info(self.metadata.name)
                            if tool_info and "file_path" in tool_info:
                                file_path = tool_info["file_path"]
                                if os.path.exists(file_path):
                                    with open(file_path, "r") as f:
                                        return f.read()
                            
                            # 如果没有找到，尝试在常见位置查找
                            possible_paths = [
                                # 优先使用工具类别的标准路径
                                os.path.join("./tools", self.metadata.category, f"{self.metadata.name}.py"),
                                # 使用当前目录
                                f"./{self.metadata.name}.py",
                                # 使用临时保存的代码（备选方案）
                                getattr(self, "_source_code", None)
                            ]
                            
                            for path in possible_paths:
                                if path and (isinstance(path, str) and os.path.exists(path)):
                                    with open(path, "r") as f:
                                        return f.read()
                                elif path and not isinstance(path, str):
                                    # 如果是_source_code属性
                                    return path
                            
                            # 如果所有尝试都失败，回退到原始方法
                            import inspect
                            return inspect.getsource(self.__class__)
                        except Exception as e:
                            print(f"Warning: Failed to read source from file: {e}")
                            # 回退到保存的源码（如果有）
                            if hasattr(self, "_source_code"):
                                return self._source_code
                            # 最后尝试使用inspect
                            import inspect
                            return inspect.getsource(self.__class__)
                    
                    # 仍然保存源码作为备选方案
                    tool_instance._source_code = code
                    
                    # 绑定新的get_source方法
                    tool_instance.get_source = get_source.__get__(tool_instance)
                    
                    return tool_instance
                else:
                    print("Failed to load temporary module.")
                    return None
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
        except Exception as e:
            print(f"Error creating tool instance: {e}")
            return None
            
    def list_available_tools(self, category: Optional[str] = None, verbose: bool = False) -> List[Dict[str, Any]]:
        """列出所有可用的工具。
        
        Args:
            category: 可选的类别过滤器。如果提供，只返回该类别的工具。
            verbose: 是否返回详细信息。如果为True，包含参数和返回值信息。
            
        Returns:
            List[Dict[str, Any]]: 工具信息列表。
        """
        # 获取所有工具名称
        tool_names = []
        if category:
            # 按类别过滤
            for name, tool in registry.tools.items():
                if tool.metadata.category == category:
                    tool_names.append(name)
        else:
            # 获取所有工具
            tool_names = list(registry.tools.keys())
        
        # 获取工具详细信息
        tools_list = []
        for name in tool_names:
            tool = registry.get_tool(name)
            if tool:
                tool_dict = tool.to_dict()
                tools_list.append(tool_dict)
        
        if not verbose:
            # 简化输出，只包含基本信息
            simplified_list = []
            for tool_data in tools_list:
                metadata = tool_data.get("metadata", {})
                simplified_list.append({
                    "name": metadata.get("name", "unknown"),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", "uncategorized"),
                    "version": metadata.get("version", "0.1.0"),
                    "dependencies": metadata.get("dependencies", []),
                    "tags": metadata.get("tags", []),
                    "author": metadata.get("author", "")
                })
            return simplified_list
        
        return tools_list
    
    def print_available_tools(self, category: Optional[str] = None):
        """打印所有可用的工具。
        
        Args:
            category: 可选的类别过滤器。如果提供，只打印该类别的工具。
        """
        tools = self.list_available_tools(category)
        
        if not tools:
            print("没有找到可用的工具。")
            return
        
        # 按类别分组
        tools_by_category = {}
        for tool in tools:
            category = tool.get("category", "uncategorized")
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool)
        
        # 打印工具信息
        print(f"找到 {len(tools)} 个可用工具:")
        for category, category_tools in tools_by_category.items():
            print(f"\n## {category.replace('_', ' ').title()} ({len(category_tools)})")
            for tool in category_tools:
                name = tool.get("name", "unknown")
                description = tool.get("description", "")
                version = tool.get("version", "")
                author = tool.get("author", "")
                tags = tool.get("tags", [])
                dependencies = tool.get("dependencies", [])
                
                print(f"- {name} (v{version}): {description}")
                if author:
                    print(f"  作者: {author}")
                if tags:
                    print(f"  标签: {', '.join(tags)}")
                if dependencies:
                    print(f"  依赖: {', '.join(dependencies)}")
    
    def get_tool_details(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取特定工具的详细信息。
        
        Args:
            tool_name: 工具名称。
            
        Returns:
            Optional[Dict[str, Any]]: 工具详细信息，如果工具不存在则返回None。
        """
        tool = registry.get_tool(tool_name)
        if not tool:
            return None
        
        # 获取工具的详细信息
        tool_dict = tool.to_dict()
        
        return tool_dict

    async def update_with_test_results(
        self,
        tool_name: str,
        test_results: str,
        output_dir: Optional[str] = None,
        register: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """Update a tool or its tests based on test results.
        
        Args:
            tool_name: The name of the tool to update.
            test_results: The pytest output from running the tests.
            output_dir: Optional directory to store the updated tool.
                       If None, uses "./tools" directory.
            register: Whether to register the updated tool.
            
        Returns:
            Tuple[bool, str, Optional[str]]: 
                - Success flag (True/False)
                - Message (success message or error details)
                - Tool name if successful, None otherwise
        """
        # Set default output directory if none is provided
        if output_dir is None:
            output_dir = "./tools"
            os.makedirs(output_dir, exist_ok=True)
            
        # Get the existing tool and its code
        try:
            tool = get_tool(tool_name, storage_dir=output_dir)
            if not tool:
                return False, f"Error: Tool '{tool_name}' not found.", None
            
            # 改为直接从文件读取源码，而不是使用tool.get_source()
            category = tool.metadata.category
            tool_file_path = os.path.join(output_dir, category, f"{tool_name}.py")
            try:
                with open(tool_file_path, "r") as f:
                    tool_code = f.read()
            except FileNotFoundError:
                return False, f"Error: Tool file not found at {tool_file_path}", None
        except Exception as e:
            return False, f"Error retrieving tool: {str(e)}", None
        
        # Get the current test code
        try:
            test_file_path = os.path.join(output_dir, tool.metadata.category, "tests", f"test_{tool_name}.py")
            try:
                with open(test_file_path, "r") as f:
                    test_code = f.read()
            except FileNotFoundError:
                test_code = ""
                print(f"Warning: No existing test file found at {test_file_path}")
        except Exception as e:
            return False, f"Error retrieving test code: {str(e)}", None
        
        # Process test results to extract the most relevant information
        processed_test_results = self._process_test_results(test_results)
        
        # Generate updated code based on test results
        try:
            update_prompt = UPDATE_WITH_TEST_RESULTS_TEMPLATE.format(
                tool_code=tool_code,
                test_code=test_code,
                test_results=processed_test_results
            )
            
            # For debugging - save update prompt to a file
            with open("update_prompt_debug.txt", "a") as f:
                f.write(update_prompt)
                
            updated_code_raw = await self._generate_code(update_prompt)
            updated_code = self._extract_code_block(updated_code_raw)
            
            if not updated_code:
                return False, "Could not extract valid Python code from the generated update.", None
        except Exception as e:
            return False, f"Error generating updated code: {str(e)}", None
        
        # Determine if the updated code is for the tool or tests
        is_test_code = "pytest" in updated_code and "test_" in updated_code
        
        if is_test_code:
            # Validate and save updated test code
            if not self.validator.validate_test(updated_code):
                return False, "Updated test code failed validation.", None
            
            # Save updated test code
            try:
                os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
                with open(test_file_path, "w") as f:
                    f.write(updated_code)
                return True, f"Updated test code saved to {test_file_path}", tool_name
            except Exception as e:
                return False, f"Error saving test code: {str(e)}", None
        else:
            # Validate updated tool code
            validation_result = self.validator.validate_tool(updated_code)
            if not validation_result:
                return False, "Updated tool code failed validation.", None
            
            # Create updated tool instance
            try:
                updated_tool = self._create_tool_instance(updated_code)
                if not updated_tool:
                    return False, "Could not create tool instance from updated code.", None
            except Exception as e:
                return False, f"Error creating tool instance: {str(e)}", None
            
            if register:
                try:
                    # Remove the old tool first
                    registry.remove_tool(tool_name, storage_dir=output_dir)
                    
                    # Register the updated tool
                    if not registry.register(updated_tool, output_dir):
                        return False, "Failed to register updated tool.", None
                    
                    return True, f"Tool updated in directory: {output_dir}", tool_name
                except Exception as e:
                    return False, f"Error registering updated tool: {str(e)}", None
            
            return True, "Tool updated successfully (not registered).", tool_name
            
    def _process_test_results(self, test_results: str) -> str:
        """Process test results to extract the most relevant information.
        
        Args:
            test_results: The raw test results from pytest.
            
        Returns:
            str: Processed test results with the most relevant information.
        """
        # If the test results are already short, return them as is
        if len(test_results.split('\n')) < 100:
            return test_results
            
        # Extract the most relevant parts of the test results
        processed_results = []
        
        # Split the test results into lines
        lines = test_results.split('\n')
        
        # Add the first few lines (summary)
        summary_lines = min(10, len(lines))
        processed_results.extend(lines[:summary_lines])
        processed_results.append("...")
        
        # Look for error and failure information
        error_sections = []
        current_section = []
        in_error_section = False
        
        for line in lines:
            # Look for lines that indicate test failures or errors
            if "FAILED" in line or "ERROR" in line or "AssertionError" in line or "E       " in line:
                if not in_error_section:
                    in_error_section = True
                    current_section = [line]
                else:
                    current_section.append(line)
            elif in_error_section:
                # If we've collected at least 3 lines and hit a blank line, end the section
                if len(current_section) >= 3 and not line.strip():
                    error_sections.append(current_section)
                    current_section = []
                    in_error_section = False
                else:
                    current_section.append(line)
        
        # Add any remaining error section
        if in_error_section and current_section:
            error_sections.append(current_section)
        
        # Add all error sections to the processed results
        for section in error_sections:
            processed_results.append("-" * 60)
            processed_results.extend(section)
        
        # Add the last few lines (summary)
        if len(lines) > 20:
            processed_results.append("...")
            processed_results.extend(lines[-10:])
        
        return "\n".join(processed_results)

    async def run_tests_and_update(
        self,
        tool_name: str,
        output_dir: Optional[str] = None,
        max_attempts: int = 3
    ) -> Tuple[bool, str]:
        """Run tests for a tool and update it based on results if needed.
        
        Args:
            tool_name: The name of the tool to test and potentially update.
            output_dir: Optional directory where the tool is stored.
                       If None, uses "./tools" directory.
            max_attempts: Maximum number of attempts to fix failing tests.
            
        Returns:
            Tuple[bool, str]: (success, message) where success indicates if all tests pass
                            and message contains test results or error information.
        """
        if output_dir is None:
            output_dir = "./tools"
        
        # Get the tool
        tool = get_tool(tool_name, storage_dir=output_dir)
        if not tool:
            return False, f"Tool '{tool_name}' not found."
        
        category = tool.metadata.category
        tool_file = os.path.join(output_dir, category, f"{tool_name}.py")
        test_file = os.path.join(output_dir, category, "tests", f"test_{tool_name}.py")
        
        # Check if test file exists
        if not os.path.exists(test_file):
            return False, f"Test file not found: {test_file}"
        
        attempt = 0
        last_error = ""
        last_test_output = ""
        
        while attempt < max_attempts:
            # Run the tests
            result = self.validator.run_tests(tool_file, test_file)
            success = result[0]
            test_output = result[1]
            last_test_output = test_output  # Save the latest test output
            
            if success:
                return True, "All tests passed successfully.\n\n" + test_output
            
            print(f"\nAttempt {attempt + 1}/{max_attempts}: Tests failed.")
            print(f"--- Test Output Summary ---")
            
            # Print a summary of the test output (first few lines)
            output_lines = test_output.split('\n')
            summary_lines = min(20, len(output_lines))  # Show at most 20 lines in the summary
            for i in range(summary_lines):
                print(output_lines[i])
            if len(output_lines) > summary_lines:
                print(f"... (and {len(output_lines) - summary_lines} more lines)")
            
            print("\nUpdating code based on test results...")
            
            # Try to update the code based on test results
            update_result = await self.update_with_test_results(
                tool_name=tool_name,
                test_results=test_output,
                output_dir=output_dir
            )
            
            success, message, updated_tool_name = update_result
            
            if not success:
                last_error = message
                print(f"Failed to update: {message}")
                attempt += 1
                continue
            
            print(f"Update successful: {message}")
            attempt += 1
        
        if last_error:
            return False, f"Failed to fix tests after {max_attempts} attempts. Last error: {last_error}\n\nLast test output:\n{last_test_output}"
        else:
            return False, f"Failed to fix tests after {max_attempts} attempts.\n\nLast test output:\n{last_test_output}" 