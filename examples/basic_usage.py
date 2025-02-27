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
    Create a tool that can perform date and time operations such as:
    - Get the current date and time
    - Convert between different time zones
    - Calculate the difference between two dates
    - Format dates in different ways
    - Add or subtract time periods from a date
    """
    
    # 获取API密钥和模型
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=openai_api_key
    )
    
    # 使用新的model_client参数初始化ToolGenerator
    generator = ToolGenerator(model_client=model_client)
    
    # 创建工具
    tool_path = generator.create_tool(spec)
    print(f"Tool created at: {tool_path}")
    
    # 工具应该已经在注册表中可用
    # 按照惯例，它将被命名为'date_time_tool'或类似名称
    return tool_path


async def use_tool_with_autogen():
    """Use the created tool in an AutoGen conversation."""
    
    # 检查文本处理工具是否存在
    text_processor = get_tool("text_processor")
    if not text_processor:
        raise ValueError("No text processor tool found in registry.")
    
    # 获取API密钥和模型
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # 创建文本处理工具函数
    def process_text(operation: str, text: str) -> str:
        """
        Process text using various operations.
        
        Args:
            operation: The operation to perform (word_count, case_upper, case_lower, extract_words, summarize)
            text: The text to process
            
        Returns:
            The result of the text processing operation as a JSON string.
        """
        result = text_processor.run(operation=operation, text=text)
        return json.dumps(result, indent=2, default=str)
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=openai_api_key
    )
    
    # 创建助手代理
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=[process_text],
        system_message="You are a helpful assistant that can use tools to process text."
    )
    
    # 创建用户代理
    user_proxy = UserProxyAgent(
        name="user",
        description="A user who needs help with text processing."
    )
    
    # 创建消息对象
    message = TextMessage(
        content="""
        Please demonstrate the text processing tool capabilities:
        1. Count the words in this message
        2. Convert this text to uppercase: "Hello, world!"
        3. Extract unique words from: "To be or not to be, that is the question."
        """,
        source="user"
    )
    
    # 启动对话
    cancellation_token = CancellationToken()
    
    # 发送消息并设置UI
    response_stream = assistant.on_messages_stream([message], cancellation_token)
    await Console(response_stream, output_stats=True)


async def use_all_tools_with_autogen():
    """Use all available tools in an AutoGen conversation."""
    
    # 获取API密钥和模型
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=openai_api_key
    )
    
    # 获取所有可用工具作为函数
    all_tools = get_all_tools_as_functions()
    
    if not all_tools:
        print("Warning: No tools found. Create some tools first.")
        return
    
    # 打印找到的工具
    print(f"Found {len(all_tools)} tools:")
    for tool in all_tools:
        print(f"- {tool.__name__}")
    
    # 创建助手代理，使用所有可用工具
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=all_tools,
        system_message="""You are a helpful assistant that can use a variety of tools to help with tasks.
You have the following tools at your disposal:
""" + "\n".join([f"- {tool.__name__}: {tool.__doc__}" for tool in all_tools])
    )
    
    # 创建用户代理
    user_proxy = UserProxyAgent(
        name="user",
        description="A user who needs help with various tasks."
    )
    
    # 创建消息对象
    message = TextMessage(
        content="""
        Hello! Please tell me what tools you have available to help me.
        Then, if available, please use an appropriate tool to help me with the current date and time.
        """,
        source="user"
    )
    
    # 启动对话
    cancellation_token = CancellationToken()
    
    # 发送消息并设置UI
    response_stream = assistant.on_messages_stream([message], cancellation_token)
    await Console(response_stream, output_stats=True)


async def main():
    """主函数，用于运行示例"""
    # 如果需要创建工具，取消下面的注释
    # await create_demo_tool()
    
    # 提供选项让用户选择要运行的示例
    print("Please select an example to run:")
    print("1. Use a specific text processing tool")
    print("2. Use all available tools")
    
    choice = input("Enter your choice (1-2): ").strip()
    
    if choice == "1":
        # 使用特定工具
        await use_tool_with_autogen()
    elif choice == "2":
        # 使用所有可用工具
        await use_all_tools_with_autogen()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    # 使用asyncio运行主函数
    asyncio.run(main()) 
