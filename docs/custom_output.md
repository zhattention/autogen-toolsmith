# 自定义输出目录

AutoGen Toolsmith 现在支持将生成的工具保存到您自己的项目目录中，而不仅仅是默认的包安装目录。此功能让您能够：

1. 将生成的工具直接集成到您自己的项目结构中
2. 更容易地版本控制和共享生成的工具
3. 为不同项目创建独立的工具集合
4. 避免修改安装包目录的权限问题

## 使用方法

在调用 `create_tool()` 或 `update_tool()` 方法时，您可以指定 `output_dir` 参数：

```python
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_toolsmith.generator import ToolGenerator

# 创建模型客户端
model_client = OpenAIChatCompletionClient(
    model="gpt-4",
    api_key="your_openai_api_key"
)

# 初始化生成器
generator = ToolGenerator(model_client=model_client)

# 定义输出目录（您自己的项目路径）
my_project_dir = Path.cwd() / "my_project"
my_project_dir.mkdir(exist_ok=True)

# 创建工具并保存到自定义目录
tool_path = generator.create_tool(
    specification="创建一个文本处理工具...",
    output_dir=my_project_dir,
    register=False  # 可选：不在全局注册表中注册
)

print(f"工具保存在: {tool_path}")
```

## 生成的目录结构

当您指定 `output_dir` 时，生成的工具文件将按以下结构组织：

```
my_project/
├── tools/
│   ├── __init__.py
│   ├── utility_tools/  # 或 data_tools, api_tools 等根据工具分类
│   │   ├── __init__.py
│   │   └── your_tool_name.py
├── tests/
│   ├── tools/
│   │   ├── utility_tools/
│   │   │   ├── __init__.py
│   │   │   └── test_your_tool_name.py
└── docs/
    └── tools/
        └── your_tool_name.md
```

系统会自动创建必要的 `__init__.py` 文件，确保您可以从您的项目中方便地导入工具：

```python
from my_project.tools.utility_tools.your_tool_name import YourToolClass
```

## 工具注册选项

在使用自定义输出目录时，您可以控制是否将工具注册到全局注册表中：

- `register=True`（默认）：工具将被注册到全局注册表中，可通过 `autogen_toolsmith.tools.get_tool()` 获取
- `register=False`：工具只会保存到指定位置，但不注册到全局注册表中

```python
# 不注册到全局注册表
tool_path = generator.create_tool(
    specification="...",
    output_dir=my_project_dir,
    register=False
)

# 使用时直接从您的项目导入
from my_project.tools.utility_tools.your_tool_name import YourToolClass
tool = YourToolClass()
```

## 完整示例

请参考 [custom_output_dir_example.py](../examples/custom_output_dir_example.py) 获取完整的示例代码。

## 注意事项

- 确保您有权限写入指定的输出目录
- 自定义输出目录中的工具在导入路径和包结构上可能与默认位置的工具有所不同
- 如果您选择不注册工具（`register=False`），则需要自行管理工具的导入和使用
- 当工具依赖其他工具时，您可能需要确保所有依赖工具都可在导入路径中找到 