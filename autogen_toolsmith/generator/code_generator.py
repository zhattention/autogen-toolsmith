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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest

from autogen_toolsmith.generator.prompt_templates import TOOL_TEMPLATE, TEST_TEMPLATE, DOCUMENTATION_TEMPLATE 
from autogen_toolsmith.storage.registry import registry, init_registry
from autogen_toolsmith.storage.versioning import version_manager
from autogen_toolsmith.tools.base.tool_base import BaseTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

class CodeValidator:
    """Validator for generated code."""
    
    @staticmethod
    def validate_syntax(code: str) -> bool:
        """Check if the code has valid Python syntax.
        
        Args:
            code: The code to validate.
            
        Returns:
            bool: True if the code has valid syntax, False otherwise.
        """
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError:
            return False
    
    @staticmethod
    def validate_security(code: str) -> Tuple[bool, str]:
        """Check if the code has potential security issues.
        
        Args:
            code: The code to validate.
            
        Returns:
            Tuple[bool, str]: A tuple of (is_safe, reason).
        """
        # This is a very basic check and should be expanded for production use
        dangerous_patterns = [
            (r"os\.system\(", "Direct system command execution"),
            (r"subprocess\.", "Subprocess execution"),
            (r"eval\(", "Code evaluation"),
            (r"exec\(", "Code execution"),
            (r"__import__\(", "Dynamic imports"),
            (r"open\(.+,\s*['\"]w['\"]", "File writing")
        ]
        
        for pattern, reason in dangerous_patterns:
            if re.search(pattern, code):
                return False, f"Security issue: {reason}"
        
        return True, ""
    
    @staticmethod
    def run_tests(tool_file: Union[str, Path], test_file: Union[str, Path]) -> Tuple[bool, str]:
        """Run tests for the generated tool.
        
        Args:
            tool_file: Path to the tool file.
            test_file: Path to the test file.
            
        Returns:
            Tuple[bool, str]: A tuple of (passed, test_output).
        """
        tool_file_path = Path(tool_file)
        test_file_path = Path(test_file)
        
        if not tool_file_path.exists():
            return False, f"Tool file not found: {tool_file_path}"
        
        if not test_file_path.exists():
            return False, f"Test file not found: {test_file_path}"
        
        # Add the tool file's directory to the Python path
        tool_dir = tool_file_path.parent
        sys.path.insert(0, str(tool_dir))
        
        try:
            # Run the tests
            result = pytest.main(["-xvs", str(test_file_path)])
            
            # Pytest exit codes: 0 = success, 1 = tests failed, 2 = errors, others = other errors
            success = result == 0
            return success, f"Tests {'passed' if success else 'failed'} with exit code {result}"
        except Exception as e:
            return False, f"Test execution error: {str(e)}"
        finally:
            # Remove the directory from the Python path
            if str(tool_dir) in sys.path:
                sys.path.remove(str(tool_dir))

    def validate_tool(self, code: str) -> bool:
        """Validate the tool code.
        
        Args:
            code: The code to validate.
            
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        # Check syntax
        if not self.validate_syntax(code):
            return False
        
        # Check security
        is_safe, _ = self.validate_security(code)
        if not is_safe:
            return False
        
        return True
        
    def validate_test(self, code: str) -> bool:
        """Validate the test code.
        
        Args:
            code: The code to validate.
            
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        # Check syntax
        if not self.validate_syntax(code):
            return False
        
        # Check security
        is_safe, _ = self.validate_security(code)
        if not is_safe:
            return False
        
        return True


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
                       If None, uses the first directory in storage_dirs.
            register: Whether to register the tool in the registry.
            
        Returns:
            Optional[str]: The path to the generated tool file if successful, None otherwise.
        """
        try:
            # Get available dependencies and existing tools information
            available_dependencies = self._get_available_dependencies()
            existing_tools_info = self._get_existing_tools_info()
            
            # Generate tool code with information about existing tools
            tool_prompt = TOOL_TEMPLATE.format(
                specification=specification,
                existing_tools_info=existing_tools_info
            )
            tool_code_raw = await self._generate_code(tool_prompt)
            
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
                tool_code=tool_code
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
            if not self.validate_tool(tool_code):
                print("Error: Generated tool code failed validation.")
                return None
            
            if not self.validate_test(test_code):
                print("Error: Generated test code failed validation.")
                return None
            
            # Create tool instance and register if requested
            tool_instance = self._create_tool_instance(tool_code)
            if not tool_instance:
                print("Error: Could not create tool instance from generated code.")
                return None
            
            if register:
                if not registry.register(tool_instance, output_dir):
                    print("Error: Failed to register tool.")
                    return None
            
            return str(registry.storage_dirs[0] / tool_metadata["category"] / f"{tool_metadata['name']}.py")
            
        except Exception as e:
            print(f"Error creating tool: {e}")
            return None

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
                       If None, uses the first directory in storage_dirs.
            register: Whether to register the updated tool.
            
        Returns:
            Optional[str]: The path to the updated tool file if successful, None otherwise.
        """
        try:
            # Get the existing tool
            existing_tool = registry.get_tool(tool_name)
            if not existing_tool:
                print(f"Error: Tool '{tool_name}' not found.")
                return None
            
            # Generate updated code
            update_prompt = UPDATE_TEMPLATE.format(
                tool_name=tool_name,
                existing_code=existing_tool.get_source(),
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
                tool_code=updated_code
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
            if not self.validate_tool(updated_code):
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
                # Remove the old tool first
                registry.remove_tool(tool_name)
                
                # Register the updated tool
                if not registry.register(updated_tool, output_dir):
                    print("Error: Failed to register updated tool.")
                    return None
            
            return str(registry.storage_dirs[0] / updated_tool.metadata.category / f"{tool_name}.py")
            
        except Exception as e:
            print(f"Error updating tool: {e}")
            return None
    
    async def generate_tool(self, specification: str, dependencies: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        生成工具代码和文档
        """
        prompt = self._prepare_prompt(specification, dependencies)
        
        # 使用await调用model_client.create
        response = await self._model_client.create(
            messages=[
                SystemMessage(
                    content=self._prompt_templates["system_message"],
                    source="system"
                ),
                UserMessage(
                    content=prompt,
                    source="user"
                )
            ]
        )
        
        # 处理返回的内容
        result = response.content if isinstance(response.content, str) else ""
        
        # 提取代码和文档
        code, doc = self._extract_code_and_doc(result)
        
        return code, doc
    
    async def generate_test(self, code: str, dependencies: Optional[Dict[str, Any]] = None) -> str:
        """
        为工具生成测试代码
        """
        prompt = self._prepare_test_prompt(code, dependencies)
        
        # 使用await调用model_client.create
        response = await self._model_client.create(
            messages=[
                SystemMessage(
                    content=self._prompt_templates["test_system_message"],
                    source="system"
                ),
                UserMessage(
                    content=prompt,
                    source="user"
                )
            ]
        )
        
        # 处理返回的内容
        result = response.content if isinstance(response.content, str) else ""
        
        # 提取测试代码
        test_code = self._extract_test_code(result)
        
        return test_code

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
                    
                    # Add the source code as an attribute
                    tool_instance._source_code = code
                    
                    # Override the get_source method
                    def get_source(self):
                        return self._source_code
                    
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
            
    def validate_tool(self, code: str) -> bool:
        """Validate the generated tool code.
        
        Args:
            code: The generated tool code.
            
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        # Check syntax
        if not self.validator.validate_syntax(code):
            print("Tool code has syntax errors.")
            return False
        
        # Check security
        is_safe, reason = self.validator.validate_security(code)
        if not is_safe:
            print(f"Tool code has security issues: {reason}")
            return False
        
        return True
    
    def validate_test(self, code: str) -> bool:
        """Validate the generated test code.
        
        Args:
            code: The generated test code.
            
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        # Check syntax
        if not self.validator.validate_syntax(code):
            print("Test code has syntax errors.")
            return False
        
        # Check security
        is_safe, reason = self.validator.validate_security(code)
        if not is_safe:
            print(f"Test code has security issues: {reason}")
            return False
        
        return True

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