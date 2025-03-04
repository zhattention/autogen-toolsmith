"""
Basic usage example for AutoGen Toolsmith.

This example shows how to:
1. Create a new tool from a specification
2. Use the tool in an AutoGen conversation
3. Use all available tools with AutoGen
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from autogen_toolsmith.generator.code_validator import CodeValidator

# 加载.env文件中的环境变量
load_dotenv()

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Import required packages
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_toolsmith import ToolGenerator, get_tool
from autogen_toolsmith.tools import BaseTool, get_all_tools_as_functions


async def create_demo_tool():
    """Create a demo date manipulation tool."""
    spec = """
    Create a tool that can get the current date and time
    The output should be a string in the format of "2025-03-03 10:00:00"
    """
    
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
    
    generator = ToolGenerator(model_client=model_client)
    
    # 创建工具
    toolname = await generator.create_tool(spec, output_dir="./tools")
    print(f"Tool created at: {toolname}")

    await generator.run_tests_and_update(toolname, output_dir="./tools")

if __name__ == "__main__":
    asyncio.run(create_demo_tool()) 
    # asyncio.run(test_tool())
    # asyncio.run(test_tool())