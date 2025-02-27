#!/usr/bin/env python
"""
枚举并使用所有可用工具的示例
=========================

此示例展示了如何:
1. 获取所有注册的工具作为函数
2. 将工具按类别组织
3. 在AutoGen Agent中使用这些工具
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 添加父目录到Python路径
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# 导入所需包
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_toolsmith import ToolGenerator
from autogen_toolsmith.tools import get_all_tools_as_functions, enumerate_tools


def print_available_tools():
    """打印所有可用工具的信息."""
    # 获取所有工具作为函数列表
    all_tools = get_all_tools_as_functions()
    
    print(f"发现 {len(all_tools)} 个注册工具:")
    for tool_func in all_tools:
        print(f"- {tool_func.__name__}: {tool_func.__doc__}")
    
    print("\n按类别组织的工具:")
    tools_by_category = enumerate_tools()
    for category, tools in tools_by_category.items():
        print(f"\n{category.upper()} ({len(tools)} 个工具):")
        for tool_func in tools:
            print(f"- {tool_func.__name__}")


async def demo_with_autogen():
    """创建一个AutoGen助手，可以使用所有可用工具."""
    # 获取API密钥和模型名称
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("请设置OPENAI_API_KEY环境变量")
    
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=openai_api_key
    )
    
    # 获取所有工具作为函数
    all_tool_functions = get_all_tools_as_functions()
    
    if not all_tool_functions:
        print("警告: 没有发现任何工具。请先创建一些工具。")
        return
    
    # 打印将要使用的工具名称
    print(f"加载了 {len(all_tool_functions)} 个工具供助手使用:")
    for tool_func in all_tool_functions:
        print(f"- {tool_func.__name__}")
    
    # 创建助手代理，使用所有可用工具
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=all_tool_functions,
        system_message="""你是一个有用的助手，可以使用多种工具来帮助用户完成任务。
你有以下工具可用:
""" + "\n".join([f"- {tool.__name__}: {tool.__doc__}" for tool in all_tool_functions])
    )
    
    # 创建用户代理
    user_proxy = UserProxyAgent(
        name="user",
        description="需要帮助解决各种问题的用户"
    )
    
    # 创建消息对象
    message = TextMessage(
        content="""
        你好! 请告诉我你可以使用哪些工具，以及每个工具的功能。
        然后，如果可用，请使用其中一个工具为我提供当前的日期和时间。
        """,
        source="user"
    )
    
    # 启动对话
    cancellation_token = CancellationToken()
    
    # 发送消息并设置UI
    response_stream = assistant.on_messages_stream([message], cancellation_token)
    await Console(response_stream, output_stats=True)


async def demo_with_category():
    """创建一个AutoGen助手，只使用特定类别的工具."""
    # 获取API密钥和模型名称
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("请设置OPENAI_API_KEY环境变量")
    
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=openai_api_key
    )
    
    # 按类别获取工具
    tools_by_category = enumerate_tools()
    
    if not tools_by_category:
        print("警告: 没有发现任何工具。请先创建一些工具。")
        return
    
    # 根据可用类别选择类别
    available_categories = list(tools_by_category.keys())
    print(f"可用工具类别: {', '.join(available_categories)}")
    
    # 如果有utility_tools类别，使用它；否则使用第一个可用类别
    category = "utility_tools" if "utility_tools" in available_categories else available_categories[0]
    category_tools = tools_by_category.get(category, [])
    
    if not category_tools:
        print(f"在'{category}'类别中没有找到工具")
        return
    
    # 打印将要使用的工具
    print(f"使用'{category}'类别中的 {len(category_tools)} 个工具:")
    for tool_func in category_tools:
        print(f"- {tool_func.__name__}")
    
    # 创建助手代理，只使用特定类别的工具
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=category_tools,
        system_message=f"""你是一个有用的助手，专注于{category}领域。
你有以下工具可用:
""" + "\n".join([f"- {tool.__name__}: {tool.__doc__}" for tool in category_tools])
    )
    
    # 创建用户代理
    user_proxy = UserProxyAgent(
        name="user",
        description=f"需要{category}相关帮助的用户"
    )
    
    # 创建消息对象
    message = TextMessage(
        content=f"""
        你好! 请展示你在{category}类别中可以使用的工具功能。
        选择一个合适的工具并展示它的使用方法。
        """,
        source="user"
    )
    
    # 启动对话
    cancellation_token = CancellationToken()
    
    # 发送消息并设置UI
    response_stream = assistant.on_messages_stream([message], cancellation_token)
    await Console(response_stream, output_stats=True)


async def main():
    """主函数，用于运行示例."""
    # 首先打印所有可用工具的信息
    print("=" * 50)
    print("查看所有可用工具:")
    print("=" * 50)
    print_available_tools()
    
    # 询问用户想要运行哪个演示
    print("\n" + "=" * 50)
    print("请选择要运行的演示:")
    print("1. 使用所有工具的助手")
    print("2. 使用特定类别工具的助手")
    print("3. 退出")
    
    choice = input("\n请输入选项 (1-3): ").strip()
    
    if choice == "1":
        print("\n" + "=" * 50)
        print("启动使用所有工具的助手...")
        print("=" * 50 + "\n")
        await demo_with_autogen()
    elif choice == "2":
        print("\n" + "=" * 50)
        print("启动使用特定类别工具的助手...")
        print("=" * 50 + "\n")
        await demo_with_category()
    else:
        print("退出程序")


if __name__ == "__main__":
    # 使用asyncio运行主函数
    asyncio.run(main()) 