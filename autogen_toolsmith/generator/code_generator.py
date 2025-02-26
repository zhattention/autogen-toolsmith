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
from autogen_toolsmith.storage.registry import registry
from autogen_toolsmith.storage.versioning import version_manager
from autogen_toolsmith.tools.base.tool_base import BaseTool


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
    def run_tests(tool_code: str, test_code: str) -> Tuple[bool, str]:
        """Run tests for the generated tool.
        
        Args:
            tool_code: The tool code.
            test_code: The test code.
            
        Returns:
            Tuple[bool, str]: A tuple of (passed, test_output).
        """
        # Create a temporary directory for the tests
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Create a module for the tool
            tool_module_path = temp_dir_path / "tool_module.py"
            with open(tool_module_path, 'w') as f:
                f.write(tool_code)
            
            # Create a test module
            test_module_path = temp_dir_path / "test_tool.py"
            with open(test_module_path, 'w') as f:
                # Adjust the import in the test code
                test_code = test_code.replace("from your_tool_module import", "from tool_module import")
                f.write(test_code)
            
            # Create an empty __init__.py to make the directory a package
            init_file = temp_dir_path / "__init__.py"
            init_file.touch()
            
            # Add the temp directory to the Python path
            sys.path.insert(0, str(temp_dir_path))
            
            try:
                # Run the tests
                result = pytest.main(["-xvs", str(test_module_path)])
                
                # Pytest exit codes: 0 = success, 1 = tests failed, 2 = errors, others = other errors
                success = result == 0
                return success, f"Tests {'passed' if success else 'failed'} with exit code {result}"
            except Exception as e:
                return False, f"Test execution error: {str(e)}"
            finally:
                # Remove the temp directory from the Python path
                sys.path.remove(str(temp_dir_path))


class ToolGenerator:
    """Generator for creating tools in the AutoGen Toolsmith system."""
    
    def __init__(self, model_client=None):
        """Initialize the tool generator.
        
        Args:
            model_client: An instance of a model client (e.g., OpenAIChatCompletionClient).
                If not provided, a default OpenAI client will be created using environment variables.
        """
        self.validator = CodeValidator()
        
        # Use provided model client if available, or create a default one
        if model_client is None:
            try:
                from autogen_ext.models.openai import OpenAIChatCompletionClient
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key is required when no model_client is provided. Set it via the OPENAI_API_KEY environment variable.")
                
                model_client = OpenAIChatCompletionClient(
                    model="gpt-4o",
                    api_key=api_key
                )
            except ImportError:
                raise ImportError("AutoGen extensions package is required. Install it with 'pip install autogen-ext'.")
        
        self.model_client = model_client
    
    def _generate_code(self, prompt: str) -> str:
        """Generate code using the model client.
        
        Args:
            prompt: The prompt to send to the model.
            
        Returns:
            str: The generated code.
        """
        response = self.model_client.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code generator for Python tools. Respond with only the code, no explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()
    
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
    
    def create_tool(self, specification: str) -> Optional[str]:
        """Create a new tool from a specification.
        
        Args:
            specification: The tool specification.
            
        Returns:
            Optional[str]: The path to the created tool file, or None if creation failed.
        """
        print(f"Generating tool from specification: {specification[:100]}...")
        
        # Get available dependencies
        dependencies = self._get_available_dependencies()
        
        # Generate tool code
        tool_prompt = TOOL_TEMPLATE.format(
            tool_specification=specification,
            available_dependencies=dependencies
        )
        
        tool_code_raw = self._generate_code(tool_prompt)
        tool_code = self._extract_code_block(tool_code_raw)
        
        # Validate tool code
        if not self.validator.validate_syntax(tool_code):
            print("Tool code has syntax errors.")
            return None
        
        is_safe, reason = self.validator.validate_security(tool_code)
        if not is_safe:
            print(f"Tool code has security issues: {reason}")
            return None
        
        # Extract the tool class name
        class_match = re.search(r"class\s+(\w+)\(BaseTool\)", tool_code)
        if not class_match:
            print("Could not extract tool class name.")
            return None
        
        tool_class_name = class_match.group(1)
        tool_name = None
        
        # Extract the tool name from the super().__init__ call
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', tool_code)
        if name_match:
            tool_name = name_match.group(1)
        
        if not tool_name:
            # Use a snake_case version of the class name if name not found
            tool_name = re.sub(r'(?<!^)(?=[A-Z])', '_', tool_class_name).lower()
            if tool_name.endswith('_tool'):
                tool_name = tool_name[:-5]
        
        # Extract the tool category
        category_match = re.search(r'category\s*=\s*["\']([^"\']+)["\']', tool_code)
        category = category_match.group(1) if category_match else "utility_tools"
        
        if category not in ["data_tools", "api_tools", "utility_tools"]:
            category = "utility_tools"
        
        # Generate test code
        test_prompt = TEST_TEMPLATE.format(tool_code=tool_code)
        test_code_raw = self._generate_code(test_prompt)
        test_code = self._extract_code_block(test_code_raw)
        
        # Run tests
        test_success, test_output = self.validator.run_tests(tool_code, test_code)
        print(f"Test results: {test_output}")
        
        if not test_success:
            print("Tool tests failed. Not registering the tool.")
            return None
        
        # Get the package directory
        package_dir = Path(__file__).parent.parent
        category_dir = package_dir / "tools" / "catalog" / category
        
        # Ensure the category directory exists
        category_dir.mkdir(exist_ok=True, parents=True)
        
        # Create an empty __init__.py file if it doesn't exist
        init_file = category_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        
        # Save the tool code
        tool_file = category_dir / f"{tool_name}.py"
        with open(tool_file, 'w') as f:
            f.write(tool_code)
        
        print(f"Tool code saved to {tool_file}")
        
        # Create a test file in the tests directory
        tests_dir = package_dir.parent / "tests" / "tools" / category
        tests_dir.mkdir(exist_ok=True, parents=True)
        
        # Create an empty __init__.py file in the tests directory if it doesn't exist
        test_init_file = tests_dir / "__init__.py"
        if not test_init_file.exists():
            test_init_file.touch()
        
        # Save the test code
        test_file = tests_dir / f"test_{tool_name}.py"
        with open(test_file, 'w') as f:
            # Adjust the import in the test code
            module_path = f"autogen_toolsmith.tools.catalog.{category}.{tool_name}"
            adjusted_test_code = test_code.replace(
                "from your_tool_module import", 
                f"from {module_path} import"
            )
            f.write(adjusted_test_code)
        
        print(f"Test code saved to {test_file}")
        
        # Generate documentation
        doc_prompt = DOCUMENTATION_TEMPLATE.format(tool_code=tool_code)
        doc_raw = self._generate_code(doc_prompt)
        
        # Save the documentation
        docs_dir = package_dir.parent / "docs" / "tools"
        docs_dir.mkdir(exist_ok=True, parents=True)
        
        doc_file = docs_dir / f"{tool_name}.md"
        with open(doc_file, 'w') as f:
            f.write(doc_raw)
        
        print(f"Documentation saved to {doc_file}")
        
        # Try to load and register the tool
        try:
            # Dynamically import the tool module
            sys.path.insert(0, str(package_dir.parent))
            module_name = f"autogen_toolsmith.tools.catalog.{category}.{tool_name}"
            module = importlib.import_module(module_name)
            
            # Find the tool class in the module
            tool_class = getattr(module, tool_class_name)
            
            # Create an instance of the tool
            tool_instance = tool_class()
            
            # Register the tool
            if registry.register(tool_instance):
                print(f"Tool {tool_name} registered successfully.")
                
                # Save the tool version
                version_id = version_manager.save_version(
                    tool_instance, 
                    tool_code, 
                    "Initial version generated from specification."
                )
                print(f"Tool version saved: {version_id}")
                
                return str(tool_file)
            else:
                print(f"Failed to register tool {tool_name}.")
                return None
        except Exception as e:
            print(f"Error registering tool: {str(e)}")
            return None
    
    def update_tool(self, tool_name: str, update_specification: str) -> Optional[str]:
        """Update an existing tool.
        
        Args:
            tool_name: The name of the tool to update.
            update_specification: The update specification.
            
        Returns:
            Optional[str]: The path to the updated tool file, or None if update failed.
        """
        # Get the existing tool
        tool = registry.get_tool(tool_name)
        if not tool:
            print(f"Tool {tool_name} not found.")
            return None
        
        # Get the existing tool source code
        source_code = registry.get_tool_source(tool_name)
        if not source_code:
            print(f"Could not retrieve source code for tool {tool_name}.")
            return None
        
        # Get available dependencies
        dependencies = self._get_available_dependencies()
        
        # Generate updated tool code
        update_prompt = f"""
You are an expert in updating Python tools. Your task is to update the following tool based on a new specification:

# Existing Tool Code
```python
{source_code}
```

# Update Specification
{update_specification}

# Available Dependencies
{dependencies}

# Output Format
Return only the updated Python code for the tool, with no additional text before or after the code.
Make sure to maintain the same class name and tool name, but update the version number appropriately.
"""
        
        updated_code_raw = self._generate_code(update_prompt)
        updated_code = self._extract_code_block(updated_code_raw)
        
        # Validate updated tool code
        if not self.validator.validate_syntax(updated_code):
            print("Updated tool code has syntax errors.")
            return None
        
        is_safe, reason = self.validator.validate_security(updated_code)
        if not is_safe:
            print(f"Updated tool code has security issues: {reason}")
            return None
        
        # Extract the tool category
        category = tool.metadata.category or "utility_tools"
        if category not in ["data_tools", "api_tools", "utility_tools"]:
            category = "utility_tools"
        
        # Generate test code
        test_prompt = TEST_TEMPLATE.format(tool_code=updated_code)
        test_code_raw = self._generate_code(test_prompt)
        test_code = self._extract_code_block(test_code_raw)
        
        # Run tests
        test_success, test_output = self.validator.run_tests(updated_code, test_code)
        print(f"Test results: {test_output}")
        
        if not test_success:
            print("Updated tool tests failed. Not updating the tool.")
            return None
        
        # Get the package directory
        package_dir = Path(__file__).parent.parent
        category_dir = package_dir / "tools" / "catalog" / category
        
        # Ensure the category directory exists
        category_dir.mkdir(exist_ok=True, parents=True)
        
        # Create an empty __init__.py file if it doesn't exist
        init_file = category_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        
        # Save the updated tool code
        tool_file = category_dir / f"{tool_name}.py"
        with open(tool_file, 'w') as f:
            f.write(updated_code)
        
        print(f"Updated tool code saved to {tool_file}")
        
        # Create a test file in the tests directory
        tests_dir = package_dir.parent / "tests" / "tools" / category
        tests_dir.mkdir(exist_ok=True, parents=True)
        
        # Create an empty __init__.py file in the tests directory if it doesn't exist
        test_init_file = tests_dir / "__init__.py"
        if not test_init_file.exists():
            test_init_file.touch()
        
        # Save the test code
        test_file = tests_dir / f"test_{tool_name}.py"
        with open(test_file, 'w') as f:
            # Adjust the import in the test code
            module_path = f"autogen_toolsmith.tools.catalog.{category}.{tool_name}"
            adjusted_test_code = test_code.replace(
                "from your_tool_module import", 
                f"from {module_path} import"
            )
            f.write(adjusted_test_code)
        
        print(f"Test code saved to {test_file}")
        
        # Generate documentation
        doc_prompt = DOCUMENTATION_TEMPLATE.format(tool_code=updated_code)
        doc_raw = self._generate_code(doc_prompt)
        
        # Save the documentation
        docs_dir = package_dir.parent / "docs" / "tools"
        docs_dir.mkdir(exist_ok=True, parents=True)
        
        doc_file = docs_dir / f"{tool_name}.md"
        with open(doc_file, 'w') as f:
            f.write(doc_raw)
        
        print(f"Documentation saved to {doc_file}")
        
        # Try to load and register the updated tool
        try:
            # Dynamically import the tool module
            sys.path.insert(0, str(package_dir.parent))
            module_name = f"autogen_toolsmith.tools.catalog.{category}.{tool_name}"
            module = importlib.import_module(module_name)
            importlib.reload(module)  # Reload to get the updated code
            
            # Extract the tool class name
            class_match = re.search(r"class\s+(\w+)\(BaseTool\)", updated_code)
            if not class_match:
                print("Could not extract tool class name from updated code.")
                return None
            
            tool_class_name = class_match.group(1)
            
            # Find the tool class in the module
            tool_class = getattr(module, tool_class_name)
            
            # Create an instance of the tool
            tool_instance = tool_class()
            
            # Register the tool
            if registry.register(tool_instance):
                print(f"Tool {tool_name} updated and registered successfully.")
                
                # Save the tool version
                version_id = version_manager.save_version(
                    tool_instance, 
                    updated_code, 
                    f"Updated based on specification: {update_specification[:50]}..."
                )
                print(f"Tool version saved: {version_id}")
                
                return str(tool_file)
            else:
                print(f"Failed to register updated tool {tool_name}.")
                return None
        except Exception as e:
            print(f"Error registering updated tool: {str(e)}")
            return None 