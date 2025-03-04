#!/usr/bin/env python
"""
示例：将生成的工具保存到自定义目录
==================================

此示例展示了如何使用ToolGenerator的output_dir参数，将生成的工具保存到您项目的自定义目录中，
而不是默认的autogen_toolsmith包目录。
"""

import asyncio
import os
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_toolsmith.generator import ToolGenerator
from dotenv import load_dotenv

async def main():
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥和模型名称
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("请设置OPENAI_API_KEY环境变量")
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model="anthropic/claude-3.7-sonnet",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": True,
            "family": "anthropic",
        },
        llm_config={
            "cache_seed": 42,
            "cache_path_root": "./cache",
        }
    )
    
    # Define multiple storage directories
    project_dir = Path.cwd() / "my_project"
    shared_dir = Path.cwd() / "shared_tools"
    
    # Create directories if they don't exist
    project_dir.mkdir(exist_ok=True, parents=True)
    shared_dir.mkdir(exist_ok=True, parents=True)
    
    # Initialize registry with multiple directories
    storage_dirs = [str(project_dir), str(shared_dir)]
    
    # Create a tool generator with custom storage directories
    generator = ToolGenerator(model_client=model_client, storage_dirs=storage_dirs)
    
    # Create a tool in the project directory
    tool_spec = """
    Create a text processing tool that can:
    1. Count words in a text
    2. Find most common words
    3. Calculate reading time
    """
    
    tool_path = await generator.create_tool(
        specification=tool_spec,
        output_dir=str(project_dir),  # Save to project directory
        register=True
    )
    
    if tool_path:
        print(f"Tool created successfully at: {tool_path}")
    
    # Create another tool in the shared directory
    shared_tool_spec = """
    Create a file utility tool that can:
    1. List files by extension
    2. Find duplicate files
    3. Calculate directory size
    """
    
    shared_tool_path = await generator.create_tool(
        specification=shared_tool_spec,
        output_dir=str(shared_dir),  # Save to shared directory
        register=True
    )
    
    if shared_tool_path:
        print(f"Shared tool created successfully at: {shared_tool_path}")
    
    # Update the tool in the project directory
    update_spec = """
    Add the following features to the text processing tool:
    1. Calculate text sentiment
    2. Extract keywords
    """
    
    updated_path = await generator.update_tool(
        tool_name="text_processor",  # Assuming this is the generated name
        update_specification=update_spec,
        output_dir=str(project_dir),  # Update in project directory
        register=True
    )
    
    if updated_path:
        print(f"Tool updated successfully at: {updated_path}")

async def test_code_validator():
    from autogen_toolsmith.generator.code_validator import CodeValidator
    validator = CodeValidator()
    validator.run_tests("./my_project/tools/utility_tools/text_formatter_tool.py", 
                        "./my_project/tests/tools/utility_tools/test_text_formatter_tool.py")

if __name__ == "__main__":
    asyncio.run(main()) 
    # asyncio.run(test_code_validator())