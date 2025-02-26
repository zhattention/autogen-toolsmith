#!/usr/bin/env python
"""
示例：将生成的工具保存到自定义目录
==================================

此示例展示了如何使用ToolGenerator的output_dir参数，将生成的工具保存到您项目的自定义目录中，
而不是默认的autogen_toolsmith包目录。
"""

import os
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_toolsmith.generator import ToolGenerator
from dotenv import load_dotenv

def main():
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥和模型名称
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请设置OPENAI_API_KEY环境变量")
    
    model = os.environ.get("OPENAI_MODEL", "gpt-4")
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key
    )
    
    # 创建工具生成器
    generator = ToolGenerator(model_client=model_client)
    
    # 定义自定义输出目录（在当前工作目录下创建my_project文件夹）
    # 您可以根据需要更改为任何目录路径
    custom_dir = Path.cwd() / "my_project"
    custom_dir.mkdir(exist_ok=True)
    
    print(f"将工具保存到自定义目录: {custom_dir}")
    
    # 创建一个简单的文本处理工具，并将其保存到自定义目录
    tool_specification = """
    创建一个名为TextFormatter的工具，它可以:
    1. 将文本转换为大写或小写
    2. 计算文本中的单词数量
    3. 删除文本中的多余空格
    4. 提取文本中的电子邮件地址和URL
    """
    
    # 使用output_dir参数将工具保存到自定义目录
    # register=False选项表示不将工具注册到全局注册表
    tool_path = generator.create_tool(
        specification=tool_specification,
        output_dir=custom_dir,
        register=False  # 可选，根据需要设置
    )
    
    if tool_path:
        print(f"工具成功创建并保存到: {tool_path}")
        print("\n自定义目录的文件结构:")
        
        # 显示生成的目录结构
        def print_directory_tree(directory, prefix=""):
            """打印目录结构"""
            print(f"{prefix}{os.path.basename(directory)}/")
            prefix += "  "
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    print_directory_tree(item_path, prefix)
                else:
                    print(f"{prefix}{item}")
        
        print_directory_tree(custom_dir)
        
        print("\n您现在可以从自定义路径导入和使用此工具:")
        print("from my_project.tools.utility_tools.text_formatter import TextFormatter")
    else:
        print("工具创建失败")

if __name__ == "__main__":
    main() 