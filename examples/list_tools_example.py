"""Example of listing and inspecting available tools."""

import sys
from autogen_toolsmith.generator import ToolGenerator

def main():
    # 创建工具生成器，不提供模型客户端
    generator = ToolGenerator()
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # 获取特定工具的详细信息
        if command == "details" and len(sys.argv) > 2:
            tool_name = sys.argv[2]
            print(f"获取工具 '{tool_name}' 的详细信息:\n")
            
            tool_details = generator.get_tool_details(tool_name)
            if tool_details:
                metadata = tool_details.get("metadata", {})
                signature = tool_details.get("signature", {})
                
                print(f"名称: {metadata.get('name', 'unknown')}")
                print(f"描述: {metadata.get('description', '')}")
                print(f"版本: {metadata.get('version', '0.1.0')}")
                print(f"作者: {metadata.get('author', '')}")
                print(f"类别: {metadata.get('category', 'uncategorized')}")
                print(f"标签: {', '.join(metadata.get('tags', []))}")
                print(f"依赖: {', '.join(metadata.get('dependencies', []))}")
                
                print("\n参数:")
                parameters = signature.get("parameters", {})
                for param_name, param_info in parameters.items():
                    param_type = param_info.get("type", "Any")
                    param_desc = param_info.get("description", "")
                    param_default = param_info.get("default", "无默认值")
                    print(f"- {param_name} ({param_type}): {param_desc}")
                    if param_default != "无默认值":
                        print(f"  默认值: {param_default}")
                
                print(f"\n返回类型: {signature.get('returns', 'Any')}")
            else:
                print(f"未找到名为 '{tool_name}' 的工具")
            
            return
        
        # 按类别列出工具
        if command == "category" and len(sys.argv) > 2:
            category = sys.argv[2]
            print(f"列出 '{category}' 类别的工具:\n")
            generator.print_available_tools(category)
            return
    
    # 默认列出所有工具
    print("列出所有可用工具:\n")
    generator.print_available_tools()
    
    print("\n使用方法:")
    print("  python list_tools_example.py                  # 列出所有工具")
    print("  python list_tools_example.py category <类别>   # 列出特定类别的工具")
    print("  python list_tools_example.py details <工具名>  # 显示特定工具的详细信息")

if __name__ == "__main__":
    main() 